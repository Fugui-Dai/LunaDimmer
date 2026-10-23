"""Luna Dimmer - 应用程序主入口与系统托盘常驻守护 (Main Entry Point & Tray Application)

功能集成：
1. QApplication 高 DPI 适配与事件循环；
2. 系统托盘图标 (QSystemTrayIcon) 与优雅右键情境菜单；
3. 全局原生热键挂载与线程安全回调派发；
4. 非破坏性生命周期双重保险：atexit 与 app.aboutToQuit 100% 还原系统背光与色彩；
5. 跨 32位/64位 Windows 平台原生无痕运行。
"""

import atexit
import ctypes
import logging
import logging.handlers
import os
import sys
from ctypes import wintypes
from typing import Dict, Optional, Any

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction

# 兼容直接通过 python src/main.py 运行
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ----------------------------------------------------------------------
# 独立崩溃守护子进程分支入口
# 必须放在任何 UI / PyQt 导入之前：守护进程只应加载 ctypes 与崩溃守护模块，
# 绝不能被拖成「半个 GUI 进程」（既拖慢启动，也让守护更易受 UI 依赖缺失牵连）。
# ----------------------------------------------------------------------
if len(sys.argv) > 1 and sys.argv[1] == "--crash-guard":
    from src.crash_guard import run_guard
    run_guard(sys.argv[2:])
    sys.exit(0)

from src.config import ConfigManager
from src.brightness_engine import BrightnessEngine
from src.overlay_window import SleepDimmerOverlay
from src.hotkey_manager import GlobalHotkeyManager
from src.main_window import LunaMainWindow
from src.i18n import t, set_language, get_system_default_language
from src.services.updater import CURRENT_VERSION
from src.styles.app_icon import create_tray_icon


def setup_logging():
    """配置控制台与文件双通道滚动日志系统 (同时支持源码运行与单文件 Exe 诊断)"""
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    logger_root = logging.getLogger()
    logger_root.setLevel(logging.INFO)

    # 1. 控制台输出 (用于 run.bat 实时查看)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger_root.addHandler(console_handler)

    # 2. 磁盘文件输出 (用于 LunaDimmer.exe 无控制台时的持久化排查)
    try:
        appdata_dir = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "LunaDimmer", "logs")
        os.makedirs(appdata_dir, exist_ok=True)
        log_file = os.path.join(appdata_dir, "luna_runtime.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=3 * 1024 * 1024,  # 单文件最大 3MB
            backupCount=3,             # 保留最多 3 个历史备份
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        logger_root.addHandler(file_handler)
        logging.info(f"LunaDimmer 日志系统已就绪，诊断日志路径: {log_file}")
    except Exception as e:
        sys.stderr.write(f"初始化磁盘日志文件异常: {e}\n")

setup_logging()
logger = logging.getLogger("LunaMain")
logging.getLogger("screen_brightness_control").setLevel(logging.ERROR)

_single_instance_mutex = None


def ensure_single_instance() -> bool:
    """确保操作系统内仅存在唯一运行的 LunaDimmer 实例 (Win32 Mutex Sentinel)"""
    global _single_instance_mutex
    if sys.platform != "win32":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        # 显式声明签名：64 位下 HANDLE 不能被默认的 c_int 截断
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        mutex_name = "Local\\LunaDimmer_SingleInstance_Mutex_2026"
        _single_instance_mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            try:
                user32 = ctypes.windll.user32
                hwnd = user32.FindWindowW(None, "月光屏幕调光器 (Luna Dimmer)")
                if not hwnd:
                    hwnd = user32.FindWindowW(None, "Luna Dimmer")
                if hwnd:
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
            return False
    except Exception as e:
        logger.warning(f"单实例互斥锁创建异常: {e}")
    return True


class LunaTrayApp:
    """Luna Dimmer 托盘常驻管理器与全应用生命周期协调者"""

    def __init__(
        self,
        main_window: LunaMainWindow,
        engine: BrightnessEngine,
        overlay: SleepDimmerOverlay,
        hotkey_mgr: GlobalHotkeyManager,
        config: ConfigManager,
    ):
        self.main_window = main_window
        self.engine = engine
        self.overlay = overlay
        self.hotkey_mgr = hotkey_mgr
        self.config = config
        self._is_cleaned_up = False

        self._init_tray_icon()
        self._init_hotkeys()
        self._register_lifecycle_handlers()

    def _init_tray_icon(self):
        """初始化右下角系统托盘图标与情境右键菜单 (全面集成 i18n 多语言)"""
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), self.main_window)
        self.tray_icon.setToolTip(t("tray_tooltip"))

        # 托盘右键菜单
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1A1A1E;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px;
                font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 180, 50, 0.25);
                color: #FFB432;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.08);
                margin: 4px 6px;
            }
        """)

        self.act_show = QAction(t("tray_show"), menu)
        self.act_show.triggered.connect(lambda: self.main_window.toggle_panel(force_show=True, from_tray=True))
        menu.addAction(self.act_show)

        menu.addSeparator()

        self.act_work = QAction(t("tray_work"), menu)
        self.act_work.setCheckable(True)
        self.act_work.triggered.connect(lambda: self.main_window.apply_scene("work"))
        menu.addAction(self.act_work)

        self.act_night = QAction(t("tray_night"), menu)
        self.act_night.setCheckable(True)
        self.act_night.triggered.connect(lambda: self.main_window.apply_scene("night"))
        menu.addAction(self.act_night)

        self.act_sleep = QAction(t("tray_sleep"), menu)
        self.act_sleep.setCheckable(True)
        self.act_sleep.triggered.connect(lambda: self.main_window.apply_scene("sleep"))
        menu.addAction(self.act_sleep)

        self.act_stealth = QAction(t("tray_stealth"), menu)
        self.act_stealth.setCheckable(True)
        self.act_stealth.triggered.connect(self.main_window.trigger_stealth_mode)
        menu.addAction(self.act_stealth)

        menu.addSeparator()

        self.act_reset = QAction(t("tray_reset"), menu)
        self.act_reset.triggered.connect(self.main_window.reset_to_system_default)
        menu.addAction(self.act_reset)

        menu.addSeparator()

        self.act_settings = QAction(t("tray_settings"), menu)
        self.act_settings.triggered.connect(self.main_window.open_settings)
        menu.addAction(self.act_settings)

        self.act_check_update = QAction(t("tray_check_update"), menu)
        self.act_check_update.triggered.connect(lambda: self.main_window.check_for_updates(silent=False))
        menu.addAction(self.act_check_update)

        self.act_feedback = QAction(t("tray_feedback", "💬 提交问题与反馈..."), menu)
        self.act_feedback.triggered.connect(self.main_window.open_feedback_dialog)
        menu.addAction(self.act_feedback)

        self.act_sponsor = QAction(t("tray_sponsor", "☕ 赞赏与心意 (请喝咖啡)..."), menu)
        self.act_sponsor.triggered.connect(self.main_window.open_sponsor_dialog)
        menu.addAction(self.act_sponsor)

        menu.addSeparator()

        self.act_exit = QAction(t("tray_exit"), menu)
        self.act_exit.triggered.connect(self.exit_application)
        menu.addAction(self.act_exit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

        if hasattr(self.main_window, "state_changed"):
            self.main_window.state_changed.connect(self.update_tray_state)
        if hasattr(self.main_window, "language_changed"):
            self.main_window.language_changed.connect(lambda lang: (self.retranslate_tray(), self.update_tray_state()))
        self.update_tray_state()

    def update_tray_tooltip(self):
        """动态刷新系统托盘悬停提示，直观呈现当前真实物理亮度、色温与运行模式"""
        b = self.engine.current_brightness
        w = self.engine.current_warmth
        if self.main_window.is_stealth_mode:
            mode_str = t("stealth_title")
        elif b < 20 or (self.engine.enhanced_2x and b < 30):
            mode_str = t("title_sleep")
        elif b > 70:
            mode_str = t("title_day")
        else:
            mode_str = t("title_night")
        tip = f"{t('app_title')} (V{CURRENT_VERSION})\n{t('brightness')}: {b}%\n{t('warmth')}: {w}%\n[{mode_str}]"
        self.tray_icon.setToolTip(tip)

    def update_tray_state(self):
        """更新托盘右键情境菜单的单选打勾态与悬停 Tooltip"""
        is_stealth = self.main_window.is_stealth_mode
        b = self.engine.current_brightness
        if hasattr(self, "act_stealth"):
            self.act_stealth.setChecked(is_stealth)
        if hasattr(self, "act_work"):
            self.act_work.setChecked(not is_stealth and b >= 85)
        if hasattr(self, "act_night"):
            self.act_night.setChecked(not is_stealth and 25 <= b <= 35)
        if hasattr(self, "act_sleep"):
            self.act_sleep.setChecked(not is_stealth and b <= 10)
        self.update_tray_tooltip()

    def retranslate_tray(self):
        """动态刷新系统托盘菜单多语言文本"""
        self.tray_icon.setToolTip(t("tray_tooltip"))
        if hasattr(self, "act_show"):
            self.act_show.setText(t("tray_show"))
            self.act_work.setText(t("tray_work"))
            self.act_night.setText(t("tray_night"))
            self.act_sleep.setText(t("tray_sleep"))
            self.act_stealth.setText(t("tray_stealth"))
            self.act_reset.setText(t("tray_reset"))
            self.act_settings.setText(t("tray_settings"))
            if hasattr(self, "act_check_update"):
                self.act_check_update.setText(t("tray_check_update"))
            if hasattr(self, "act_feedback"):
                self.act_feedback.setText(t("tray_feedback", "💬 提交问题与反馈..."))
            if hasattr(self, "act_sponsor"):
                self.act_sponsor.setText(t("tray_sponsor", "☕ 赞赏与心意 (请喝咖啡)..."))
            self.act_exit.setText(t("tray_exit"))

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """鼠标左键单击托盘图标时呼出或收起面板"""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.main_window.toggle_panel(from_tray=True)

    def _init_hotkeys(self):
        """
        挂载后台全局快捷键。

        快捷键的「动作 → 回调」映射表已收敛到 `LunaMainWindow._hotkey_callbacks()` 单一真相源，
        此处不再维护第二份表，避免两处逐渐漂移（此前就漏掉过 toggle_spotlight）。
        回调的跨线程投递由主窗口内部的 GuiDispatcher 负责（信号队列 → Qt 主事件循环）。
        """
        if not self.hotkey_mgr:
            return
        try:
            self.main_window.register_all_hotkeys()
            self.hotkey_mgr.start()
        except Exception as e:
            logger.warning("Failed to start hotkey manager: %s", e)

    def _register_lifecycle_handlers(self):
        """注册全生命周期双重保险，保障异常或正常退出时 100% 还原系统背光"""
        atexit.register(self.cleanup)
        qapp = QApplication.instance()
        if qapp:
            qapp.aboutToQuit.connect(self.cleanup)

    def exit_application(self):
        """用户主动请求退出程序"""
        self.cleanup()
        qapp = QApplication.instance()
        if qapp:
            qapp.quit()

    def cleanup(self):
        """执行彻底恢复并关闭所有窗体与监听线程"""
        if self._is_cleaned_up:
            return
        self._is_cleaned_up = True
        logger.info("Executing clean exit restoration protocol...")

        # 写入 clean_exit.flag 通知后台独立崩溃守护进程本次为主程序正常退出
        try:
            appdata = os.getenv("APPDATA", os.path.expanduser("~"))
            clean_flag_file = os.path.join(appdata, "LunaDimmer", "clean_exit.flag")
            with open(clean_flag_file, "w", encoding="utf-8") as f:
                f.write("clean")
        except Exception:
            pass

        try:
            if self.hotkey_mgr:
                self.hotkey_mgr.stop()
        except Exception as e:
            logger.warning("Error stopping hotkey manager: %s", e)

        try:
            if self.main_window:
                self.main_window.cleanup_and_restore()
                self.main_window.close()
        except Exception as e:
            logger.warning("Error cleaning main window: %s", e)

        try:
            if self.overlay:
                self.overlay.close()
        except Exception as e:
            logger.warning("Error closing overlay: %s", e)

        try:
            if self.tray_icon:
                self.tray_icon.hide()
        except Exception as e:
            logger.warning("Error hiding tray icon: %s", e)

        # 终极保险：还原系统硬件背光与 Gamma
        try:
            self.engine.restore_on_exit()
        except Exception as e:
            logger.warning("Error during final engine restore: %s", e)


def setup_crash_handlers(engine: BrightnessEngine):
    """注册全局未捕获异常急救钩子：主进程异常崩溃时立即无痕还原屏幕物理亮度和色温"""
    def global_excepthook(exc_type, exc_value, exc_traceback):
        logger.critical("Unhandled exception caught in main process, executing crash recovery...", exc_info=(exc_type, exc_value, exc_traceback))
        try:
            engine.restore_on_exit()
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = global_excepthook


def spawn_crash_guard(engine: BrightnessEngine) -> None:
    """启动独立进程级崩溃守护者，即使主进程遭遇强行闪退/kill也能在毫秒级还原屏幕物理亮度和色温"""
    if engine.mock_hardware:
        return
    try:
        import subprocess
        from src.win32_compat import save_backup_gamma_to_file

        appdata = os.getenv("APPDATA", os.path.expanduser("~"))
        target_dir = os.path.join(appdata, "LunaDimmer")
        os.makedirs(target_dir, exist_ok=True)

        gamma_file = os.path.join(target_dir, "crash_gamma_backup.json")
        clean_flag_file = os.path.join(target_dir, "clean_exit.flag")

        # 启动前清理旧的 clean_exit.flag
        if os.path.exists(clean_flag_file):
            try:
                os.remove(clean_flag_file)
            except Exception:
                pass

        save_backup_gamma_to_file(gamma_file)

        pid = os.getpid()
        init_b = engine.initial_brightness

        creation_flags = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | DETACHED_PROCESS

        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--crash-guard", str(pid), str(init_b), gamma_file, clean_flag_file]
            popen_kwargs = {}
        else:
            # 源码运行必须显式指定工作目录，否则从桌面快捷方式/计划任务启动时
            # cwd 可能是 System32，`-m src.crash_guard` 会因找不到包而静默失败。
            cmd = [sys.executable, "-m", "src.crash_guard", str(pid), str(init_b), gamma_file, clean_flag_file]
            popen_kwargs = {"cwd": _project_root}

        subprocess.Popen(
            cmd,
            creationflags=creation_flags,
            close_fds=True,
            **popen_kwargs,
        )
        logger.info("Crash guardian sentinel spawned successfully.")
    except Exception as e:
        logger.warning(f"Failed to spawn crash guardian: {e}")


def create_application_components(
    mock_hardware: bool = False,
    config: Optional[ConfigManager] = None,
) -> Dict[str, Any]:
    """
    装配并初始化 Luna Dimmer 核心组件树工厂函数（支持单元测试与生产运行）：
    返回包含 config, engine, overlay, hotkey_mgr, main_window, tray_app 的字典。
    """
    cfg = config or ConfigManager()
    initial_lang = cfg.get("language") or get_system_default_language()
    set_language(initial_lang)

    engine = BrightnessEngine(mock_hardware=mock_hardware, config=cfg)
    setup_crash_handlers(engine)
    spawn_crash_guard(engine)
    overlay = SleepDimmerOverlay()
    hotkey_mgr = GlobalHotkeyManager()

    main_win = LunaMainWindow(
        config=cfg,
        engine=engine,
        overlay=overlay,
        hotkey_mgr=hotkey_mgr,
    )
    main_win.retranslate_ui(initial_lang)

    tray_app = LunaTrayApp(
        main_window=main_win,
        engine=engine,
        overlay=overlay,
        hotkey_mgr=hotkey_mgr,
        config=cfg,
    )

    return {
        "config": cfg,
        "engine": engine,
        "overlay": overlay,
        "hotkey_mgr": hotkey_mgr,
        "main_window": main_win,
        "tray_app": tray_app,
    }


def main():
    """主程序启动入口"""
    if not ensure_single_instance():
        logger.warning("LunaDimmer 实例已在运行中，激活已有窗口并退出多余进程。")
        sys.exit(0)
    # 启用高分屏高 DPI 缩放渲染
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 注册 Windows AppUserModelID 保证任务栏独占图标与 Alt+Tab 预览
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LunaDimmer.App.2026")
        except Exception:
            pass

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(create_tray_icon())

    # 全局设置系统抗锯齿字体 (跨 Windows 7 / 10 / 11 字体回退保障)
    from src.win32_compat import get_windows_version_name
    primary_font = "Microsoft YaHei" if get_windows_version_name() == "win7" else "Microsoft YaHei UI"
    font = QFont(primary_font, 9)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    components = create_application_components(mock_hardware=False)
    main_win = components["main_window"]

    # 开机自启静默模式检测（严格兑现“Windows 登录后自动最小化常驻托盘，不弹窗打扰”的大厂承诺）
    is_silent = any(arg in sys.argv for arg in ("--silent", "--minimized", "-s"))
    if not is_silent:
        main_win.toggle_panel(force_show=True, from_tray=True)
    else:
        logger.info("LunaDimmer 随系统开机静默启动，常驻系统托盘就绪。")
    # 每次进入程序均在后台静默检查更新（结果仅在偏好设置页面呈现，不打扰首页）
    QTimer.singleShot(1000, lambda: main_win.check_for_updates(silent=True))

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
