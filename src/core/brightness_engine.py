"""Luna Dimmer - 核心调光引擎与非破坏性生命周期恢复 (Brightness Engine & Lifecycle)

支持双轨无缝调光（物理背光 + 软件遮罩）、2x 深度压暗芯片算法与退出/崩溃 100% 无痕还原。

线程模型：
- DDC/CI 硬件通信统一投递到后台守护线程队列，GUI 主线程永不阻塞；
- Gamma 色温写入做 40ms 节流 + 尾部兜底补写，既保证拖动顺滑又保证最终值必达；
- `restore_on_exit` 会先停用引擎、取消待写入、join 硬件线程，再同步还原，
  彻底消除「退出瞬间被后台线程写回暗值」的竞态。
"""

import logging
import queue
import threading
import time
from typing import Optional, Tuple

from src.platform.win32_compat import backup_system_gamma, restore_system_gamma, set_display_gamma_ramp

try:
    from src.core.config import ConfigManager
except ImportError:  # pragma: no cover - 避免循环导入
    ConfigManager = None  # type: ignore

logger = logging.getLogger("LunaEngine")

# 硬件调光最小间隔（DDC/CI I2C 慢速总线防堵塞）
_HW_MIN_INTERVAL = 0.04
# Gamma 色温写入最小间隔
_GAMMA_MIN_INTERVAL = 0.04
# 尾部补写延迟
_GAMMA_TRAILING_DELAY = 0.06


class BrightnessEngine:
    """
    Luna 核心调光引擎：
    - 管理物理硬件背光与软件全屏穿透遮罩的双轨计算；
    - 管理 2x 深度压暗芯片算法（硬件加速下潜 + 遮罩提前深度介入）；
    - 管理屏幕琥珀色温与 Gamma 协调联动；
    - 记录系统初始状态快照，在软件退出或崩溃时无损还原系统初始状态，使软件设置全部失效。
    - 首次启动默认按照屏幕硬件亮度得来，不手动设置，不区分白夜；调节亮度即刻持久化保存。
    """

    def __init__(self, mock_hardware: bool = False, config: Optional["ConfigManager"] = None):
        self.mock_hardware = mock_hardware
        self.config = config

        self.initial_brightness = 100
        self.current_brightness = 100
        self.current_warmth = 0
        self.enhanced_2x = False
        self.target_display = None  # None: 全部同步, 0: 主屏独立, 1: 副屏独立
        self.has_hardware_support = True

        self._engine_active = True
        self._last_gamma_apply = 0.0
        self._gamma_timer: Optional[threading.Timer] = None
        self._last_warmth_applied: Optional[int] = None

        # 1. 第一时间记录并备份系统启动物理快照（非 mock 环境）
        if not self.mock_hardware:
            try:
                backup_system_gamma()
            except Exception as e:
                logger.warning("备份系统 Gamma 曲线失败: %s", e)
            self._capture_initial_brightness()

        # 2. 读取配置：
        # - 若之前调节过亮度（saved_b is not None），下次启动就显示上次保存的亮度；
        # - 若首次启动（saved_b is None），默认按照屏幕得来，不要手动设置，不区分白夜。
        saved_b = None
        if self.config is not None:
            saved_b = self.config.get("brightness")
            self.current_warmth = max(0, min(100, int(self.config.get("warmth", 0) or 0)))
            self.enhanced_2x = bool(self.config.get("enhanced_2x", False))

        if saved_b is not None:
            self.current_brightness = max(1, min(100, int(saved_b)))
        else:
            self.current_brightness = max(1, min(100, int(self.initial_brightness)))

        hw, ov = self.compute_levels(self.current_brightness, self.enhanced_2x)
        self._current_hw = hw
        self._current_ov = ov
        self._last_hw_time = 0.0
        self._last_applied_hw = -1
        self._last_save_time = 0.0
        self._last_warmth_save_time = 0.0

        # 初始化异步 DDC/CI 硬件通信工作队列与守护线程，彻底避免硬件 I2C 慢速通信阻塞 GUI 主线程
        self._hw_worker_running = True
        self._hw_queue: "queue.Queue" = queue.Queue(maxsize=1)
        self._hw_worker_thread = threading.Thread(
            target=self._hw_worker_loop,
            daemon=True,
            name="LunaHwBrightnessWorker",
        )
        self._hw_worker_thread.start()

        # 若加载的是用户上次保存的自定义亮度，应用到硬件显示器
        if not self.mock_hardware and saved_b is not None:
            try:
                import screen_brightness_control as sbc
                sbc.set_brightness(hw)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 硬件异步工作线程
    # ------------------------------------------------------------------
    def _hw_worker_loop(self) -> None:
        """后台异步硬件通信工作线程，聚合最新调光指令，避免阻塞 GUI 主线程与 DDC/CI 总线堵塞"""
        while self._hw_worker_running:
            try:
                task = self._hw_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if task is None or not self._hw_worker_running:
                try:
                    self._hw_queue.task_done()
                except ValueError:
                    pass
                break

            hw_val, display_idx = task
            try:
                import screen_brightness_control as sbc
                if display_idx is not None:
                    sbc.set_brightness(hw_val, display=display_idx)
                else:
                    sbc.set_brightness(hw_val)
                self._last_applied_hw = hw_val
            except Exception:
                pass
            finally:
                try:
                    self._hw_queue.task_done()
                except ValueError:
                    pass

    def _capture_initial_brightness(self) -> None:
        """捕获系统初始硬件亮度快照，若硬件不支持或抛出异常则以 100% 全亮为基准并标记无硬件支持"""
        self.has_hardware_support = False
        try:
            import screen_brightness_control as sbc
            levels = sbc.get_brightness()
            if levels:
                val = levels[0] if isinstance(levels, (list, tuple)) else levels
                if isinstance(val, (int, float)) and 1 <= val <= 100:
                    self.initial_brightness = int(val)
                    self.has_hardware_support = True
                    return
        except Exception as e:
            logger.info("未检测到 DDC/CI 硬件背光通道，将使用软件遮罩兜底: %s", e)
        self.initial_brightness = 100
        self.has_hardware_support = False

    # ------------------------------------------------------------------
    # 双轨算法
    # ------------------------------------------------------------------
    def compute_levels(self, brightness: int, enhanced_2x: bool) -> Tuple[int, float]:
        """
        计算 (硬件背光百分比 0-100, 软件透明遮罩不透明度 0.0-0.80)
        全架构自适应 (Windows 7 / Windows 10 / Windows 11)：
        - 人机安全可视底限 (Safe Visual Floor, RFC-21):
          日常滑块调光不透明度严格限制在 0.80 (2x模式下 0.82)，保留 18%~20% 物理微光与文字可读性，
          彻底解决用户滑到极低亮度时屏幕漆黑一片无法看清界面的脱困死局；
        - 纯黑黑屏挂机模式 (0.995 纯黑) 仅由特定挂机功能 (SleepDimmerOverlay.trigger_stealth_mode) 独立调用。
        """
        b = max(1, min(100, int(round(brightness))))

        # 硬件不受支持时的平滑软件兜底（完美保障 Windows 7 等环境）
        if not getattr(self, "has_hardware_support", True):
            hw = b
            ov = min(0.80, round((100 - b) / 99.0 * 0.80, 4)) if b < 100 else 0.0
            return hw, ov

        if enhanced_2x:
            # 2x 深度压暗曲线：硬件背光加速压减（40%即下潜至0），遮罩提前平滑介入，最高限制在 0.82 人机安全底限
            if b >= 40:
                hw = int(round((b - 40) / 60.0 * 100))
                ov = 0.0
            else:
                hw = 0
                ov = min(0.82, round(0.18 + (40 - b) / 39.0 * 0.64, 4))
        else:
            # 标准无缝双轨曲线：10%~100% 硬件无缝调节，1%~10% 软件遮罩平滑介入，最高限制在 0.80 人机安全底限
            if b >= 10:
                hw = int(b)
                ov = 0.0
            else:
                hw = 0
                ov = min(0.80, round(0.15 + (10 - b) / 9.0 * 0.65, 4))

        return hw, ov

    # ------------------------------------------------------------------
    # 亮度
    # ------------------------------------------------------------------
    def set_brightness(self, value: int, enhanced_2x: Optional[bool] = None, force_hw: bool = False) -> Tuple[int, float]:
        """
        调节屏幕亮度并更新硬件/遮罩状态。
        支持 DDC/CI I2C 硬件通信防丢包节流与即调即存。
        """
        if enhanced_2x is not None:
            self.enhanced_2x = bool(enhanced_2x)

        self.current_brightness = max(1, min(100, int(round(value))))
        hw, ov = self.compute_levels(self.current_brightness, self.enhanced_2x)
        self._current_hw = hw
        self._current_ov = ov

        now = time.time()
        # DDC/CI I2C 慢速串行总线防堵塞节流与后台异步非阻塞调度
        if self._engine_active and not self.mock_hardware and getattr(self, "has_hardware_support", True):
            if force_hw or (now - getattr(self, "_last_hw_time", 0.0) >= _HW_MIN_INTERVAL and hw != getattr(self, "_last_applied_hw", -1)):
                self._last_hw_time = now
                # 提交硬件调光任务至守护线程工作队列，丢弃滞后的旧任务保证实时响应
                try:
                    if self._hw_queue.full():
                        try:
                            self._hw_queue.get_nowait()
                            self._hw_queue.task_done()
                        except Exception:
                            pass
                    self._hw_queue.put_nowait((hw, self.target_display))
                except Exception:
                    pass

        if self.config is not None:
            self.config.set("brightness", self.current_brightness)
            self.config.set("enhanced_2x", self.enhanced_2x)
            if force_hw or (now - getattr(self, "_last_save_time", 0.0) >= 0.2):
                self.config.save()
                self._last_save_time = now

        return hw, ov

    # ------------------------------------------------------------------
    # 多显示器
    # ------------------------------------------------------------------
    def get_display_count(self) -> int:
        """获取当前系统连接的物理显示器数量"""
        if self.mock_hardware:
            return 2
        try:
            import screen_brightness_control as sbc
            monitors = sbc.list_monitors()
            return max(1, len(monitors))
        except Exception:
            return 1

    def cycle_display_target(self) -> Tuple[Optional[int], str]:
        """在 '全屏同步' 与 '各独立显示器' 之间循环切换调光作用域"""
        count = self.get_display_count()
        if count <= 1:
            self.target_display = None
            return None, "🖥️=🖥️ 同步"

        if self.target_display is None:
            self.target_display = 0
            return 0, "🖥️¹ 主屏独立"
        elif self.target_display + 1 < count:
            self.target_display += 1
            return self.target_display, f"🖥️{self.target_display + 1} 副屏独立"
        else:
            self.target_display = None
            return None, "🖥️=🖥️ 全屏同步"

    def get_display_brightness(self, display_idx: Optional[int] = None) -> int:
        """获取目标显示器当前真实的物理背光亮度"""
        if self.mock_hardware:
            return self.current_brightness
        try:
            import screen_brightness_control as sbc
            if display_idx is not None:
                levels = sbc.get_brightness(display=display_idx)
            else:
                levels = sbc.get_brightness()
            if levels:
                val = levels[0] if isinstance(levels, (list, tuple)) else levels
                return int(val)
        except Exception:
            pass
        return self.current_brightness

    def sync_from_display(self, display_idx: Optional[int] = None) -> int:
        """
        切换调光作用域后，把面板状态同步为目标显示器此刻的真实物理亮度。

        只做状态对齐（重算双轨层级 + 更新界面数值），**不向硬件回写**，
        避免在切换作用域的瞬间把某块屏幕的背光改掉。
        """
        brightness = max(1, min(100, int(self.get_display_brightness(display_idx))))
        self.current_brightness = brightness
        hw, ov = self.compute_levels(brightness, self.enhanced_2x)
        self._current_hw = hw
        self._current_ov = ov
        return brightness

    # ------------------------------------------------------------------
    # 色温
    # ------------------------------------------------------------------
    def _apply_gamma(self, warmth: Optional[int] = None) -> bool:
        """同步写入 Gamma 色温曲线（内部方法，绝不抛异常）"""
        if not self._engine_active or self.mock_hardware:
            return False
        target = self.current_warmth if warmth is None else int(warmth)
        try:
            ok = set_display_gamma_ramp(target)
        except Exception as e:
            logger.warning("写入 Gamma 曲线失败: %s", e)
            return False
        self._last_gamma_apply = time.time()
        self._last_warmth_applied = target
        return bool(ok)

    def _schedule_gamma_apply(self) -> None:
        """节流窗口内被丢弃的色温写入，通过一次性守护定时器做尾部兜底补写"""
        if self._gamma_timer is not None:
            return
        timer = threading.Timer(_GAMMA_TRAILING_DELAY, self._delayed_gamma_apply)
        timer.daemon = True
        timer.name = "LunaGammaTrailing"
        self._gamma_timer = timer
        timer.start()

    def _delayed_gamma_apply(self) -> None:
        self._gamma_timer = None
        if not self._engine_active:
            return
        if self._last_warmth_applied == self.current_warmth:
            return
        self._apply_gamma(self.current_warmth)

    def set_warmth(self, value: int, force_save: bool = False) -> bool:
        """
        调节琥珀护眼色温 (0~100)。

        采用 40ms 节流 + 尾部兜底补写：拖动时不会对 GDI 造成每次移动都写 LUT 的压力，
        松手 / 强制保存时立即写入，保证最终一帧的色彩一定生效。
        """
        new_value = max(0, min(100, int(round(value))))
        self.current_warmth = new_value
        success = True

        if self.mock_hardware:
            self._last_warmth_applied = new_value
        else:
            now = time.time()
            if force_save or (now - self._last_gamma_apply >= _GAMMA_MIN_INTERVAL):
                success = self._apply_gamma(new_value)
            else:
                self._schedule_gamma_apply()

        if self.config is not None:
            self.config.set("warmth", self.current_warmth)
            now = time.time()
            if force_save or (now - getattr(self, "_last_warmth_save_time", 0.0) >= 0.2):
                self.config.save()
                self._last_warmth_save_time = now

        return bool(success)

    # ------------------------------------------------------------------
    # 组合调控
    # ------------------------------------------------------------------
    def set_enhanced_2x(self, enabled: bool) -> Tuple[int, float]:
        """切换 2x 深度压暗芯片状态"""
        return self.set_brightness(self.current_brightness, enhanced_2x=enabled)

    def apply(self, brightness: int, warmth: int, enhanced_2x: bool) -> Tuple[int, float]:
        """综合应用亮度、色温与 2x 增强设置"""
        self.set_warmth(warmth)
        return self.set_brightness(brightness, enhanced_2x=enhanced_2x)

    def get_hardware_brightness(self) -> int:
        """获取当前硬件背光目标亮度 (0~100)"""
        return self._current_hw

    def get_overlay_opacity(self) -> float:
        """获取当前软件遮罩不透明度 (0.0~0.995)"""
        return self._current_ov

    @property
    def hardware_brightness(self) -> int:
        return self._current_hw

    @property
    def overlay_opacity(self) -> float:
        return self._current_ov

    # ------------------------------------------------------------------
    # 生命周期还原
    # ------------------------------------------------------------------
    def restore_on_exit(self) -> None:
        """
        非破坏性生命周期恢复协议：
        软件退出或崩溃时 100% 无损还原系统硬件初始物理亮度及原始 Gamma 色温曲线，
        使软件所设置的全部调光与色温效果立即失效。
        """
        # 1. 先停用引擎，阻断任何后续后台写入（含尾部 Gamma 补写定时器）
        self._engine_active = False
        timer = self._gamma_timer
        self._gamma_timer = None
        if timer is not None:
            try:
                timer.cancel()
            except Exception:
                pass

        # 2. 终止异步硬件调光后台工作线程，清空遗留任务并等待其真正退出
        self._hw_worker_running = False
        try:
            while not self._hw_queue.empty():
                try:
                    self._hw_queue.get_nowait()
                    self._hw_queue.task_done()
                except Exception:
                    break
            self._hw_queue.put_nowait(None)
        except Exception:
            pass

        worker = getattr(self, "_hw_worker_thread", None)
        if worker is not None and worker.is_alive():
            try:
                worker.join(timeout=1.5)
            except Exception:
                pass

        # 3. 同步且确定性还原系统初始物理亮度与原始 Gamma 曲线
        if not self.mock_hardware:
            try:
                import screen_brightness_control as sbc
                sbc.set_brightness(self.initial_brightness)
            except Exception:
                pass
            try:
                restore_system_gamma()
            except Exception:
                pass

        self.current_brightness = self.initial_brightness
        self._current_hw = self.initial_brightness
        self._current_ov = 0.0
        self.current_warmth = 0
        self.enhanced_2x = False
        self._last_applied_hw = -1
        self._last_warmth_applied = 0
