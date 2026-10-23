from typing import Optional
"""
全屏无感穿透暗夜遮罩窗口 (Sleep Dimmer Overlay)
覆盖所有连接显示器，支持平滑透明度渐变、纯黑隐身模式与贝塞尔曲线防眩目平滑苏醒。
"""

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QPoint, QRectF
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QColor, QPainter, QRadialGradient, QBrush
from src.platform.win32_compat import set_window_transparent_clickthrough


class SleepDimmerOverlay(QWidget):
    """
    全屏半透明暗夜遮罩层：
    1. 覆盖所有外接与内置显示器的虚拟桌面全屏区域；
    2. 无边框置顶、透明不激活、完全穿透所有鼠标及键盘操作；
    3. 集成平滑缓动动画引擎（OutCubic 贝塞尔过渡曲线）；
    4. 支持一键纯黑隐身 (99.5% 遮光) 与 1.5 秒平滑柔和苏醒。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self._opacity = 0.0
        self._flashlight_pos = None

        # 铺满全桌面（多屏幕虚拟桌面边界）
        self._update_geometry()

        # 监听屏幕分辨率或多显示器拓扑变动
        primary = QApplication.primaryScreen()
        if primary:
            try:
                primary.virtualGeometryChanged.connect(self._update_geometry)
            except Exception:
                pass

        # 动效引擎（采用三次贝塞尔缓动曲线）
        self.anim = QPropertyAnimation(self, b"dim_opacity")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(self._on_animation_finished)

    def _update_geometry(self):
        """根据当前主屏幕及扩展屏幕的虚拟几何全景覆盖窗口区域并加固穿透"""
        primary = QApplication.primaryScreen()
        if primary:
            screen_geo = primary.virtualGeometry()
            self.setGeometry(screen_geo)
        else:
            self.setGeometry(QRect(0, 0, 1920, 1080))
        if self._opacity <= 0.001 and self.isVisible():
            self.hide()
        elif self.isVisible():
            try:
                hwnd = int(self.winId())
                set_window_transparent_clickthrough(hwnd)
            except Exception:
                pass

    def refresh_geometry(self) -> None:
        """
        公开的几何刷新入口。

        屏幕热插拔 / 分辨率变化时由主窗口调用；直接操作 `_update_geometry`
        属于跨对象的私有方法访问，容易在重构中悄悄失效，故提供正式接口。
        """
        self._update_geometry()

    def _on_animation_finished(self):
        """动画结束时，若不透明度已降至 0，则自动隐藏窗口释放系统合成开销"""
        if self._opacity <= 0.001 and self.isVisible():
            self.hide()

    def showEvent(self, event):
        """显示窗口时调用 Windows 底层 API 进行分层穿透加固，确保 100% 穿透"""
        super().showEvent(event)
        try:
            hwnd = int(self.winId())
            set_window_transparent_clickthrough(hwnd)
        except Exception:
            pass

    def get_dim_opacity(self) -> float:
        """获取当前遮罩不透明度"""
        return self._opacity

    def set_dim_opacity(self, val: float):
        """设置当前遮罩不透明度并触发重绘（限制在 [0.0, 0.995] 范围内）"""
        self._opacity = max(0.0, min(0.995, float(val)))
        self.update()

    dim_opacity = pyqtProperty(float, get_dim_opacity, set_dim_opacity)

    @property
    def current_opacity(self) -> float:
        """读取当前遮罩不透明度属性"""
        return self._opacity

    def set_target_opacity(self, opacity: float, animate: bool = False, duration: int = 400):
        """
        设置目标透明度：
        :param opacity: 目标透明度 (0.0 ~ 0.995)
        :param animate: 是否启用平滑过渡动画
        :param duration: 动画时长 (ms)
        """
        target = max(0.0, min(0.995, float(opacity)))
        if not animate:
            self.anim.stop()
            self.set_dim_opacity(target)
            if target > 0 and not self.isVisible():
                self.show()
            elif target <= 0.001 and self.isVisible():
                self.hide()
        else:
            if not self.isVisible() and target > 0:
                self.show()
            self.anim.stop()
            self.anim.setDuration(duration)
            self.anim.setStartValue(self._opacity)
            self.anim.setEndValue(target)
            self.anim.start()

    def set_opacity_animated(self, opacity: float, duration_ms: int = 400):
        """平滑动画调节透明度快捷方法"""
        self.set_target_opacity(opacity, animate=True, duration=duration_ms)

    def trigger_stealth_mode(self, opacity: float = 0.995):
        """进入纯黑隐身模式（默认 99.5% 墨黑沉浸，夜间听歌/挂机睡眠防刺眼）"""
        self.set_target_opacity(opacity, animate=True, duration=800)

    def wake_up_with_bezier(self, target_opacity: float = 0.0):
        """1.5 秒三次贝塞尔平滑苏醒，防骤亮强光刺激视网膜"""
        self.set_target_opacity(target_opacity, animate=True, duration=1500)

    def set_flashlight_pos(self, pos: Optional[QPoint]):
        """设置光标微光探照灯中心坐标，若为 None 则关闭探照灯"""
        if self._flashlight_pos != pos:
            self._flashlight_pos = pos
            self.update()

    def paintEvent(self, event):
        """重绘事件：若不透明度极低则跳过，支持全屏纯黑与鼠标微光探照灯柔和光晕"""
        if self._opacity <= 0.001:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        alpha = max(0, min(255, int(self._opacity * 255)))

        if self._flashlight_pos and self._opacity > 0.5:
            # 开启微光探照灯光晕：全屏深黑背景中在鼠标位置柔和透光
            painter.fillRect(self.rect(), QColor(0, 0, 0, alpha))
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            rad_grad = QRadialGradient(QRectF(self._flashlight_pos.x() - 100, self._flashlight_pos.y() - 100, 200, 200).center(), 100)
            rad_grad.setColorAt(0.0, QColor(0, 0, 0, int(alpha * 0.90)))
            rad_grad.setColorAt(0.6, QColor(0, 0, 0, int(alpha * 0.45)))
            rad_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(rad_grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self._flashlight_pos, 100, 100)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, alpha))


OverlayWindow = SleepDimmerOverlay
