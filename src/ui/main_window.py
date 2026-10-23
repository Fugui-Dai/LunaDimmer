"""Luna Dimmer - 苹果控制中心风格深色毛玻璃主面板 (Main Window & Settings)

融合腾讯 T-Star / 红点奖级设计语言：
1. Apple Liquid Dark Glass 多层立体磨砂玻璃 (rgba(22, 22, 26, 0.90))；
2. 22px 连续超椭圆圆角与 0.5px 顶部/边缘折射光晕 (Rim Light)；
3. 拟态天体核心 (LivingLuminary) 随亮度与模式动态演进 (日冕/弦月/12秒微光脉动)；
4. 硬件与软件遮罩一体化 CapsuleSlider 胶囊滑块；
5. 2x 深度压暗流光微芯片 (ToggleChip ⚡)；
6. 智能多屏拓扑感知徽标 [ 🖥️=🖥️ 同步 ]；
7. 睡前纯黑挂机磁贴 [ 🎧 纯黑挂机 (黑屏听歌) ] 与防刺眼贝塞尔渐变苏醒；
8. 偏好设置弹窗 (全局热键展示与 Windows 开机自启配置)。
"""

from typing import Optional, Dict, Any, Callable
import copy
import math
import logging

from PyQt5.QtCore import Qt, QPoint, QRectF, QPointF, QTimer, QEvent, QObject, pyqtSignal
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QLinearGradient,
    QRadialGradient,
    QPainterPath,
    QFont,
    QCursor,
    QKeyEvent,
)
from src.i18n import t, get_language, set_language
from src.updater import CURRENT_VERSION, UpdateWorker, UpgradeDialog, is_newer_version
from PyQt5.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QAbstractButton,
    QDialog,
    QGraphicsDropShadowEffect,
    QApplication,
)

from src.config import ConfigManager, DEFAULT_SCENE_PRESETS
from src.brightness_engine import BrightnessEngine
from src.overlay_window import SleepDimmerOverlay
from src.styles.app_icon import create_app_icon
from src.hotkey_manager import GlobalHotkeyManager
from src.widgets.living_luminary import LivingLuminary
from src.widgets.capsule_slider import CapsuleSlider
from src.widgets.toggle_chip import ToggleChip
from src.widgets.luminary_hud import LuminaryHUD
from src.settings_dialog import SettingsDialog


class LunaCardFrame(QFrame):
    """苹果深空多层磨砂玻璃卡片背景与超椭圆边缘光 (Squircle Liquid Glass Container)"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_Hover, True)
        self.theme = "dark"

    def mousePressEvent(self, event):
        if self.parent() and hasattr(self.parent(), "mousePressEvent"):
            self.parent().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.parent() and hasattr(self.parent(), "mouseMoveEvent"):
            self.parent().mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.parent() and hasattr(self.parent(), "mouseReleaseEvent"):
            self.parent().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        rect = QRectF(self.rect())

        # 24px 连续平滑超椭圆 (Apple Continuous Squircle，对标网页端 border-radius: 24px)
        path = QPainterPath()
        path.addRoundedRect(rect, 24.0, 24.0)

        # 1. 主基底：黑天暗夜黑曜石 vs 白夜雪山瓷白 vs 苹果高通透液态玻璃
        cur_th = getattr(self, "theme", "dark")
        bg_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if cur_th == "light":
            # 苹果白天模式：纯净雪瓷微透高光底衬 (Apple System Light Background)
            bg_grad.setColorAt(0.0, QColor(255, 255, 255, 252))
            bg_grad.setColorAt(0.5, QColor(246, 246, 248, 250))
            bg_grad.setColorAt(1.0, QColor(242, 242, 246, 252))
        elif cur_th == "liquid_glass":
            # 苹果 VisionOS / Sequoia 高通透冰晶液态玻璃 (纯正物理光学介质，剔除浑浊深蓝)
            bg_grad.setColorAt(0.0, QColor(32, 36, 48, 175))
            bg_grad.setColorAt(0.5, QColor(22, 26, 36, 185))
            bg_grad.setColorAt(1.0, QColor(14, 16, 24, 195))
        else:
            # 苹果深色模式：中性纯正黑曜云石底板 (Apple System Charcoal Obsidian)
            bg_grad.setColorAt(0.0, QColor(36, 36, 38, 240))
            bg_grad.setColorAt(0.5, QColor(28, 28, 30, 245))
            bg_grad.setColorAt(1.0, QColor(20, 20, 22, 250))
        painter.fillPath(path, bg_grad)

        # 2. 天顶环境漫反射 (Ambient Top Specular Glow)
        top_glow = QRadialGradient(rect.width() * 0.35, 0, rect.width() * 0.7)
        if cur_th == "light":
            top_glow.setColorAt(0.0, QColor(255, 255, 255, 80))
            top_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        elif cur_th == "liquid_glass":
            top_glow.setColorAt(0.0, QColor(255, 255, 255, 38))
            top_glow.setColorAt(0.45, QColor(255, 255, 255, 12))
            top_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        else:
            top_glow.setColorAt(0.0, QColor(255, 255, 255, 20))
            top_glow.setColorAt(0.5, QColor(255, 255, 255, 6))
            top_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillPath(path, QBrush(top_glow))

        # 3. 双层复合物理微折射边框 (Dual-layer Rim Light)
        if cur_th == "light":
            outer_pen = QPen(QColor(0, 0, 0, 24), 1.0)
        elif cur_th == "liquid_glass":
            outer_pen = QPen(QColor(255, 255, 255, 45), 1.0)
        else:
            outer_pen = QPen(QColor(0, 0, 0, 95), 1.0)
        painter.setPen(outer_pen)
        painter.drawPath(path)

        # 内层 0.8px 晶体高光倒角折射线 (Specular Rim Light)
        inner_rect = rect.adjusted(0.8, 0.8, -0.8, -0.8)
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner_rect, 21.2, 21.2)

        rim_grad = QLinearGradient(0, 0, 0, rect.height())
        if cur_th == "light":
            rim_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
            rim_grad.setColorAt(0.2, QColor(255, 255, 255, 140))
            rim_grad.setColorAt(0.8, QColor(255, 255, 255, 40))
            rim_grad.setColorAt(1.0, QColor(0, 0, 0, 16))
        elif cur_th == "liquid_glass":
            rim_grad.setColorAt(0.0, QColor(255, 255, 255, 220))   # 顶部晶体全反射切角
            rim_grad.setColorAt(0.18, QColor(255, 255, 255, 90))
            rim_grad.setColorAt(0.70, QColor(255, 255, 255, 25))
            rim_grad.setColorAt(1.0, QColor(255, 255, 255, 50))   # 底部微晶通透折射 (物理纯白，无荧光蓝)
        else:
            rim_grad.setColorAt(0.0, QColor(255, 255, 255, 60))
            rim_grad.setColorAt(0.15, QColor(255, 255, 255, 24))
            rim_grad.setColorAt(0.70, QColor(255, 255, 255, 8))
            rim_grad.setColorAt(1.0, QColor(255, 255, 255, 14))

        inner_pen = QPen(QBrush(rim_grad), 0.8)
        painter.setPen(inner_pen)
        painter.drawPath(inner_path)


class GuiDispatcher(QObject):
    """
    跨线程 GUI 投递器（全局热键安全桥梁）。

    背景：Win32 全局热键的回调由 `GlobalHotkeyManager` 的后台消息泵线程执行。
    该线程只有裸 Win32 消息循环、没有 Qt 事件循环，因此在那里调用
    `QTimer.singleShot(0, func)` 的定时器永远不会触发；即使触发也是跨线程操作 QWidget。
    正确做法是让回调只做一件事：通过 Qt 信号把可调用对象排队投递回主线程执行。
    """

    _posted = pyqtSignal(object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        # 显式 QueuedConnection：无论从哪个线程 emit，槽函数都在本对象所属（GUI）线程执行
        self._posted.connect(self._run, Qt.QueuedConnection)

    def _run(self, func: Callable[[], None]) -> None:
        try:
            func()
        except Exception:
            logging.getLogger("LunaGui").exception("热键回调执行异常")

    def post(self, func: Callable[[], None]) -> None:
        """线程安全地把回调投递到 Qt 主事件循环"""
        self._posted.emit(func)


class WindowControlDot(QAbstractButton):
    """
    苹果 macOS 标准风格自绘控制按钮：
    - 严格对齐 Apple 原生尺寸：直径 12px、间距 8px（两两圆心距 20px）；
    - 矢量内嵌图标尺寸 1:1 对标 macOS 原生 Traffic Lights（叉号跨度 5px、横线 6px、齿轮外径 6px）；
    - 采用 QPainter 硬件抗锯齿几何自绘，高分屏下毫无虚化与重影。
    """

    def __init__(self, dot_type: str = "close", tooltip: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.dot_type = dot_type  # "settings", "min", "close"
        self._hovered = False
        # 苹果 macOS 标准规格：圆点尺寸严格为 12x12
        self.setFixedSize(12, 12)
        self.setCursor(Qt.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 1. 苹果 macOS 原生交通信号灯色值
        if self.dot_type == "settings":
            bg = QColor("#2EE64A") if self._hovered else QColor("#27C93F")
            border = QColor(26, 171, 41, 230 if self._hovered else 180)
            symbol_color = QColor("#00380B")
        elif self.dot_type == "min":
            bg = QColor("#FFCA45") if self._hovered else QColor("#FFBD2E")
            border = QColor(222, 161, 35, 230 if self._hovered else 180)
            symbol_color = QColor("#543500")
        else:  # "close"
            bg = QColor("#FF6E67") if self._hovered else QColor("#FF5F56")
            border = QColor(224, 68, 62, 230 if self._hovered else 180)
            symbol_color = QColor("#4A0002")

        # 2. 绘制圆点底色 (精准 12x12，圆心为 6.0, 6.0)
        rect = QRectF(0.5, 0.5, 11.0, 11.0)
        p.setBrush(QBrush(bg))
        p.setPen(QPen(border, 0.75))
        p.drawEllipse(rect)

        # 3. 绘制纯几何矢量内嵌符号 (默认常驻清晰显示，悬浮时微强化)
        cx, cy = 6.0, 6.0
        p.setBrush(Qt.NoBrush)
        pen_width = 1.35 if self._hovered else 1.15
        sym_col = symbol_color if self._hovered else QColor(symbol_color.red(), symbol_color.green(), symbol_color.blue(), 215)

        if self.dot_type == "settings":
            # 矢量精密 6 齿对称微型齿轮 (直径 6px，与横线和叉号等比例对齐)
            pen = QPen(sym_col, pen_width, Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            p.drawEllipse(QRectF(cx - 1.3, cy - 1.3, 2.6, 2.6))
            for i in range(6):
                angle = i * (math.pi / 3.0)
                x1 = cx + 1.8 * math.cos(angle)
                y1 = cy + 1.8 * math.sin(angle)
                x2 = cx + 3.0 * math.cos(angle)
                y2 = cy + 3.0 * math.sin(angle)
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        elif self.dot_type == "min":
            # 矢量水平居中微横线 (跨度 6px，对标苹果横线尺度)
            pen = QPen(sym_col, pen_width, Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(cx - 3.0, cy), QPointF(cx + 3.0, cy))

        elif self.dot_type == "close":
            # 矢量 45° 精密对称微叉号 (跨度 5px，对标苹果关闭叉号尺度)
            pen = QPen(sym_col, pen_width, Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            d = 2.5
            p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
            p.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))


class StealthActionCard(QAbstractButton):
    """苹果级黑屏挂机双行磁贴 (1:1 对标网页端双行分阶排版：标题 13px #E6E6EC，副标题 11.5px #94A3B8)"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False
        self.theme = "dark"

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 13.0, 13.0)

        is_pressed = self.isDown()
        cur_th = getattr(self, "theme", "dark")

        if cur_th == "light":
            if is_pressed:
                painter.setBrush(QBrush(QColor(0, 0, 0, 20)))
                painter.setPen(QPen(QColor(0, 0, 0, 45), 1.0))
            elif self._hovered:
                painter.setBrush(QBrush(QColor(0, 0, 0, 10)))
                painter.setPen(QPen(QColor(0, 0, 0, 35), 1.0))
            else:
                painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
                painter.setPen(QPen(QColor(0, 0, 0, 22), 1.0))
            painter.drawPath(path)
            title_color = QColor(29, 29, 31)
            sub_color = QColor(100, 116, 139)
        elif cur_th == "liquid_glass":
            bg_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            if is_pressed:
                bg_grad.setColorAt(0.0, QColor(255, 180, 50, 40))
                bg_grad.setColorAt(1.0, QColor(255, 150, 20, 18))
                painter.setPen(QPen(QColor(255, 195, 80, 100), 1.0))
            elif self._hovered:
                bg_grad.setColorAt(0.0, QColor(255, 195, 80, 50))
                bg_grad.setColorAt(1.0, QColor(255, 160, 40, 20))
                painter.setPen(QPen(QColor(255, 195, 80, 120), 1.0))
            else:
                bg_grad.setColorAt(0.0, QColor(255, 255, 255, 28))
                bg_grad.setColorAt(1.0, QColor(255, 255, 255, 10))
                painter.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
            painter.setBrush(QBrush(bg_grad))
            painter.drawPath(path)
            title_color = QColor(255, 255, 255)
            sub_color = QColor(186, 230, 253, 210)
        else:
            # 苹果黑天模式 (135deg 线性微质感渐变 + 悬浮金光边缘)
            bg_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            if is_pressed:
                bg_grad.setColorAt(0.0, QColor(255, 180, 50, 30))
                bg_grad.setColorAt(1.0, QColor(255, 150, 20, 12))
                painter.setBrush(QBrush(bg_grad))
                painter.setPen(QPen(QColor(255, 195, 80, 100), 1.0))
            elif self._hovered:
                bg_grad.setColorAt(0.0, QColor(255, 195, 80, 41))
                bg_grad.setColorAt(1.0, QColor(255, 160, 40, 13))
                painter.setBrush(QBrush(bg_grad))
                painter.setPen(QPen(QColor(255, 195, 80, 115), 1.0))
            else:
                bg_grad.setColorAt(0.0, QColor(255, 255, 255, 18))
                bg_grad.setColorAt(1.0, QColor(255, 255, 255, 5))
                painter.setBrush(QBrush(bg_grad))
                painter.setPen(QPen(QColor(255, 255, 255, 26), 1.0))
            painter.drawPath(path)

            # Top rim highlight
            if not self._hovered and not is_pressed:
                rim_pen = QPen(QColor(255, 255, 255, 56), 1.0)
                painter.setPen(rim_pen)
                painter.drawLine(int(rect.left() + 13), int(rect.top()), int(rect.right() - 13), int(rect.top()))
            elif self._hovered:
                rim_pen = QPen(QColor(255, 215, 120, 165), 1.0)
                painter.setPen(rim_pen)
                painter.drawLine(int(rect.left() + 13), int(rect.top()), int(rect.right() - 13), int(rect.top()))

            title_color = QColor(230, 230, 236) if not self._hovered else QColor(255, 255, 255)
            sub_color = QColor(148, 163, 184)

        # 2. Draw 2-tier text matching Web CSS
        title_font = QFont("Microsoft YaHei UI")
        title_font.setPixelSize(14)
        title_font.setWeight(QFont.Medium)

        sub_font = QFont("Microsoft YaHei UI")
        sub_font.setPixelSize(12)
        sub_font.setWeight(QFont.Normal)

        # Line 1: Title
        painter.setFont(title_font)
        painter.setPen(title_color)
        title_rect = QRectF(rect.x(), rect.y() + 8.0, rect.width(), 18.0)
        painter.drawText(title_rect, Qt.AlignCenter, t("stealth_title"))

        # Line 2: Subtitle
        painter.setFont(sub_font)
        painter.setPen(sub_color)
        sub_rect = QRectF(rect.x(), rect.y() + 27.0, rect.width(), 16.0)
        painter.drawText(sub_rect, Qt.AlignCenter, t("stealth_sub"))

        painter.end()


class LunaMainWindow(QWidget):
    """
    Luna Dimmer 苹果风格主控制中心面板：
    - 无边框标准窗口任务栏呈现，支持流畅拖拽移动与托盘智能停靠；
    - 联动拟态天体核心与无缝双轨调光滑块；
    - 2x 深度压暗微芯片与三行情境胶囊；
    - 睡前纯黑挂机与全桌面事件感知防刺眼苏醒；
    - 完整中英文国际化 (i18n) 动态即时切换。
    """

    language_changed = pyqtSignal(str)
    state_changed = pyqtSignal()

    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        engine: Optional[BrightnessEngine] = None,
        overlay: Optional[SleepDimmerOverlay] = None,
        hotkey_mgr: Optional[GlobalHotkeyManager] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.config = config or ConfigManager()
        self.engine = engine or BrightnessEngine(mock_hardware=True, config=self.config)
        self.overlay = overlay or SleepDimmerOverlay()
        self.hotkey_mgr = hotkey_mgr

        self.is_stealth_mode = False
        self._stealth_start_time = 0.0
        self._stealth_mouse_start_pos = None
        self.current_theme = str(self.config.get("theme", "dark"))
        self.current_scene_key = "work"
        self._stealth_poll_timer = QTimer(self)
        self._stealth_poll_timer.setInterval(50)
        self._stealth_poll_timer.timeout.connect(self._check_stealth_mouse_wiggle)
        self._drag_pos = QPoint()

        # 全局热键回调的跨线程安全投递器（必须是本窗口的子对象，天然归属 GUI 线程）
        self._gui_dispatcher = GuiDispatcher(self)
        self._spotlight_active = False
        self._spotlight_timer = QTimer(self)
        self._spotlight_timer.setInterval(30)
        self._spotlight_timer.timeout.connect(self._update_spotlight_pos)

        self._setup_window_attributes()
        self._init_ui()
        self.hud = LuminaryHUD()
        self._load_initial_state()
        qapp = QApplication.instance()
        if qapp:
            try:
                qapp.screenAdded.connect(self._on_screens_changed)
                qapp.screenRemoved.connect(self._on_screens_changed)
            except Exception:
                pass

    def paintEvent(self, event):
        """确保窗口背景四角 100% 透明，彻底清除 DWM 黑底直角阴影"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    def _setup_window_attributes(self):
        """配置苹果现代卡片窗口属性（无边框、标准窗口任务栏、透明背景、托盘精准停靠）"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Window
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowTitle(t("app_full_title"))
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(474, 608)

    def _init_ui(self):
        """初始化多层磨砂玻璃与苹果风格布局体系"""
        # 外层根布局，预留 14px / 16px 留白空间渲染扩散式超柔和阴影
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 16, 14, 16)
        root_layout.setSpacing(0)

        # 核心毛玻璃卡片容器 (对标网页端 446px x 576px 舒适尺寸)
        self.card = LunaCardFrame(self)
        self.card.setObjectName("centralCard")
        self.card.setFixedSize(446, 576)
        self.card.setStyleSheet('font-family: "Segoe UI", "Microsoft YaHei UI", -apple-system, sans-serif;')

        # 28px 弥散环境光阴影 (0 8px 32px rgba(0, 0, 0, 0.45))
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.card.setGraphicsEffect(shadow)

        # 卡片内部垂直流布局：对标网页端 padding: 20px 舒适留白
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. 顶部 Header (LivingLuminary 呼吸球 + 标题状态 + 工具按钮)
        # -------------------------------------------------------------
        header_vbox = QVBoxLayout()
        header_vbox.setContentsMargins(0, 0, 0, 0)
        header_vbox.setSpacing(14)  # 充裕的呼吸间距，彻底消除“离设置/最小化/关闭太近”的问题

        # 1.1 顶行 (Top Row)：拟态天体核心 + 主标题 + 最右上角窗口控制组
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)

        # 拟态天体核心
        self.luminary = LivingLuminary(self.card)
        top_row.addWidget(self.luminary, 0, Qt.AlignVCenter)

        # 主标题 (随语言动态显示：中文为 月光屏幕调光器，英文为 Luna Dimmer)
        self.lbl_title = QLabel(t("app_title"), self.card)
        font_title = QFont("Microsoft YaHei UI", 13, QFont.Bold)
        font_title.setStyleStrategy(QFont.PreferAntialias)
        self.lbl_title.setFont(font_title)
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 700; letter-spacing: 0.3px;")
        self.lbl_title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        top_row.addWidget(self.lbl_title, 0, Qt.AlignVCenter)

        top_row.addStretch()

        # 最右上角窗口控制组 (设置 最小化 关闭)
        self.window_controls_group = QWidget(self.card)
        self.window_controls_group.setObjectName("windowControlsGroup")
        ctrl_layout = QHBoxLayout(self.window_controls_group)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(8)

        # 1.1 绿色按钮：偏好设置与全局热键
        self.btn_settings = WindowControlDot("settings", "偏好设置与全局热键", self.window_controls_group)
        self.btn_settings.clicked.connect(self.open_settings)
        ctrl_layout.addWidget(self.btn_settings)

        # 1.2 黄色按钮：最小化到系统托盘
        self.btn_minimize = WindowControlDot("min", "最小化到系统托盘", self.window_controls_group)
        self.btn_minimize.clicked.connect(lambda: self.toggle_panel(force_show=False))
        ctrl_layout.addWidget(self.btn_minimize)

        # 1.3 红色按钮：关闭并退出程序
        self.btn_close = WindowControlDot("close", "退出软件 (100% 恢复系统初始屏幕亮度与色彩)", self.window_controls_group)
        self.btn_close.clicked.connect(self.exit_app)
        ctrl_layout.addWidget(self.btn_close)

        top_row.addWidget(self.window_controls_group, 0, Qt.AlignRight | Qt.AlignVCenter)
        header_vbox.addLayout(top_row)

        # 1.2 次级功能行 (Sub Row)：【日间工作模式】与【深色/恢复原状】严格位于同一水平基准线，绝对对齐
        sub_action_row = QHBoxLayout()
        sub_action_row.setContentsMargins(0, 0, 0, 0)
        sub_action_row.setSpacing(6)
        sub_action_row.setAlignment(Qt.AlignVCenter)

        # 左侧缩进，与天体球对齐并与上方主标题文字左边沿完全对齐 (天体球38px + 间距12px = 50px)
        sub_action_row.addSpacing(50)

        # 动态模式状态 (日间工作模式)
        self.lbl_status = QLabel(t("status_day"), self.card)
        font_status = QFont("Segoe UI Emoji", 10)
        font_status.setStyleStrategy(QFont.PreferAntialias)
        self.lbl_status.setFont(font_status)
        self.lbl_status.setStyleSheet("color: rgba(235, 235, 245, 0.75); font-size: 13.5px; font-weight: 500;")
        self.lbl_status.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        sub_action_row.addWidget(self.lbl_status, 0, Qt.AlignVCenter)

        sub_action_row.addStretch()

        # 多显示器智能感知徽标（支持点击切换调光范围）
        self.multi_monitor_badge = ToggleChip(
            text=t("display_sync"),
            parent=self.card,
            is_checkable=False,
        )
        self.multi_monitor_badge.setFixedHeight(24)
        self.multi_monitor_badge.setToolTip("点击切换调光作用域：全屏同步 / 主屏独立 / 副屏独立")
        self.multi_monitor_badge.clicked.connect(self._on_multi_monitor_clicked)
        self.multi_monitor_badge.setVisible(False)
        sub_action_row.addWidget(self.multi_monitor_badge, 0, Qt.AlignVCenter)

        # 1.2.1 极简静默更新胶囊 (Non-intrusive Update Pill) - 发现新版时安静呈现，绝不弹窗打扰
        self.btn_update_pill = QPushButton("🚀 有更新", self.card)
        self.btn_update_pill.setObjectName("btnUpdatePill")
        self.btn_update_pill.setToolTip("发现新版本，点击查看更新日志")
        self.btn_update_pill.setFixedHeight(25)
        self.btn_update_pill.setCursor(Qt.PointingHandCursor)
        self.btn_update_pill.setStyleSheet("""
            QPushButton#btnUpdatePill {
                background: rgba(10, 132, 255, 0.16);
                border: 1px solid rgba(10, 132, 255, 0.42);
                border-radius: 12px;
                color: #38BDF8;
                font-family: "Segoe UI Emoji", "Microsoft YaHei UI", -apple-system, sans-serif;
                font-size: 12.5px;
                font-weight: 600;
                padding: 1px 10px;
            }
            QPushButton#btnUpdatePill:hover {
                background: rgba(10, 132, 255, 0.32);
                border-color: #38BDF8;
                color: #FFFFFF;
            }
            QPushButton#btnUpdatePill:pressed {
                background: rgba(10, 132, 255, 0.48);
            }
        """)
        self.btn_update_pill.setVisible(False)
        self.btn_update_pill.clicked.connect(self._on_update_pill_clicked)
        sub_action_row.addWidget(self.btn_update_pill, 0, Qt.AlignVCenter)

        # 主题快速切换胶囊 (1:1 对标网页端快捷切换：🌙 深色 / ☀️ 浅色 / 💧 玻璃)
        th_labels = {"dark": t("theme_dark"), "light": t("theme_light"), "liquid_glass": t("theme_liquid_glass")}
        self.btn_theme_toggle = QPushButton(th_labels.get(self.current_theme, t("theme_dark")), self.card)
        self.btn_theme_toggle.setObjectName("btnThemeToggle")
        self.btn_theme_toggle.setToolTip("快捷切换深色、浅色与液态玻璃主题")
        self.btn_theme_toggle.setFixedHeight(25)
        self.btn_theme_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_theme_toggle.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
                color: rgba(235, 235, 245, 0.85);
                font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 2px 12px;
            }
            QPushButton:hover {
                background: rgba(245, 179, 56, 0.18);
                border-color: rgba(245, 179, 56, 0.48);
                color: #F5B338;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.18);
            }
        """)
        self.btn_theme_toggle.clicked.connect(self._cycle_theme_quick)
        sub_action_row.addWidget(self.btn_theme_toggle, 0, Qt.AlignVCenter)

        # 一键恢复原状按钮 ↺ (Apple 极简灵动微晶胶囊，告别笨重长方体)
        self.btn_reset = QPushButton("↺ 恢复原状", self.card)
        self.btn_reset.setObjectName("btnReset")
        self.btn_reset.setToolTip("一键恢复屏幕亮度和色温为系统初始状态")
        self.btn_reset.setFixedHeight(25)
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: rgba(235, 235, 245, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
                font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 2px 12px;
            }
            QPushButton:hover {
                background: rgba(245, 179, 56, 0.18);
                border-color: rgba(245, 179, 56, 0.48);
                color: #F5B338;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.18);
            }
        """)
        self.btn_reset.clicked.connect(self.reset_to_system_default)
        sub_action_row.addWidget(self.btn_reset, 0, Qt.AlignVCenter)

        header_vbox.addLayout(sub_action_row)

        card_layout.addLayout(header_vbox)
        card_layout.addStretch(1)

        # -------------------------------------------------------------
        # 2. 光感亮度区 (CapsuleSlider + 2x 深度压暗微芯片)
        # -------------------------------------------------------------
        bright_section = QVBoxLayout()
        bright_section.setContentsMargins(0, 0, 0, 0)
        bright_section.setSpacing(0)

        bright_header = QHBoxLayout()
        bright_header.setContentsMargins(0, 0, 0, 0)
        bright_header.setAlignment(Qt.AlignVCenter)

        self.lbl_bright_title = QLabel(t("brightness"), self.card)
        self.lbl_bright_title.setFixedHeight(22)
        self.lbl_bright_title.setStyleSheet("color: #CBD5E1; font-size: 14px; font-weight: 500; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")
        bright_header.addWidget(self.lbl_bright_title)

        bright_header.addStretch()

        # 深度压暗微芯片 (对标网页端 ⚡ 深度压暗 ⚡)
        self.chip_2x = ToggleChip(
            text=t("boost_2x"),
            icon_symbol="",
            parent=self.card,
            is_checkable=True,
        )
        self.chip_2x.setFixedHeight(24)
        self.chip_2x.toggled.connect(self.set_enhanced_2x)
        bright_header.addWidget(self.chip_2x)

        bright_section.addLayout(bright_header)
        bright_section.addSpacing(8)

        # 屏幕亮度胶囊大滑块 (44px 黄金触控标准)
        self.brightness_slider = CapsuleSlider(
            title=t("brightness"),
            icon_symbol="☀️",
            min_val=1,
            max_val=100,
            parent=self.card,
            accent_mode="brightness",
        )
        self.brightness_slider.valueChanged.connect(self.set_brightness)
        self.brightness_slider.sliderReleased.connect(lambda: (self.engine.set_brightness(self.brightness_slider.value(), force_hw=True), self.config.save()))
        bright_section.addWidget(self.brightness_slider)

        card_layout.addLayout(bright_section)
        card_layout.addStretch(1)

        # -------------------------------------------------------------
        # 3. 护眼色温区 (CapsuleSlider 防蓝光滑块 + 舒缓防蓝光可点击微芯片)
        # -------------------------------------------------------------
        warmth_section = QVBoxLayout()
        warmth_section.setContentsMargins(0, 0, 0, 0)
        warmth_section.setSpacing(0)

        warmth_header = QHBoxLayout()
        warmth_header.setContentsMargins(0, 0, 0, 0)
        warmth_header.setAlignment(Qt.AlignVCenter)

        self.lbl_warmth_title = QLabel(t("warmth"), self.card)
        self.lbl_warmth_title.setFixedHeight(22)
        self.lbl_warmth_title.setStyleSheet("color: #CBD5E1; font-size: 14px; font-weight: 500; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")
        warmth_header.addWidget(self.lbl_warmth_title)
        warmth_header.addStretch()

        # 舒缓防蓝光微芯片 (与 ⚡ 深度压暗 ⚡ 1:1 对仗，支持点击一键开启/关闭 50% 护眼防蓝光)
        self.chip_warmth = ToggleChip(
            text=t("warmth_chip"),
            icon_symbol="",
            parent=self.card,
            is_checkable=True,
        )
        self.chip_warmth.setFixedHeight(24)
        self.chip_warmth.setToolTip("点击一键开启/关闭 50% 舒缓防蓝光模式")
        self.chip_warmth.toggled.connect(self._on_chip_warmth_toggled)
        warmth_header.addWidget(self.chip_warmth)

        warmth_section.addLayout(warmth_header)
        warmth_section.addSpacing(8)

        self.warmth_slider = CapsuleSlider(
            title=t("warmth"),
            icon_symbol="🕯️",
            min_val=0,
            max_val=100,
            parent=self.card,
            accent_mode="warmth",
        )
        self.warmth_slider.valueChanged.connect(self.set_warmth)
        self.warmth_slider.sliderReleased.connect(lambda: (self.engine.set_warmth(self.warmth_slider.value(), force_save=True), self.config.save()))
        warmth_section.addWidget(self.warmth_slider)

        card_layout.addLayout(warmth_section)
        card_layout.addStretch(1)

        # -------------------------------------------------------------
        # 4. 常用场景预设 (Quick Scene Presets: 2 行 3 列微晶网格 + 自由管理)
        # -------------------------------------------------------------
        presets_section = QVBoxLayout()
        presets_section.setContentsMargins(0, 0, 0, 0)
        presets_section.setSpacing(0)

        presets_header = QHBoxLayout()
        presets_header.setContentsMargins(0, 0, 0, 0)
        presets_header.setAlignment(Qt.AlignVCenter)

        self.lbl_presets_title = QLabel(t("presets_title"), self.card)
        self.lbl_presets_title.setFixedHeight(22)
        self.lbl_presets_title.setStyleSheet("color: #CBD5E1; font-size: 14px; font-weight: 500; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")
        presets_header.addWidget(self.lbl_presets_title)

        presets_header.addStretch()

        # ⚙️ 自定义与管理预设按钮 (Apple 微晶灵动药丸，对标网页端)
        self.btn_manage_presets = QPushButton(t("manage_presets"), self.card)
        self.btn_manage_presets.setObjectName("btnManagePresets")
        self.btn_manage_presets.setCursor(Qt.PointingHandCursor)
        self.btn_manage_presets.setFixedHeight(24)
        self.btn_manage_presets.setToolTip("自定义全部场景预设的名称、目标亮度、色温与深度压暗")
        self.btn_manage_presets.setStyleSheet("""
            QPushButton {
                background: rgba(245, 179, 56, 0.14);
                color: #F5B338;
                border: 1px solid rgba(245, 179, 56, 0.40);
                border-radius: 12px;
                font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 2px 12px;
            }
            QPushButton:hover {
                background: rgba(245, 179, 56, 0.24);
                color: #FBBF24;
                border-color: rgba(245, 179, 56, 0.65);
            }
            QPushButton:pressed {
                background: rgba(245, 179, 56, 0.35);
            }
        """)
        self.btn_manage_presets.clicked.connect(lambda: self.open_preset_customizer())
        presets_header.addWidget(self.btn_manage_presets)

        presets_section.addLayout(presets_header)
        presets_section.addSpacing(8)

        # 第一行预设：白天办公、夜间阅读、睡前极暗
        scene_layout_1 = QHBoxLayout()
        scene_layout_1.setSpacing(10)

        self.pill_work = ToggleChip(text=t("preset_work"), icon_symbol="☀️", parent=self.card, is_checkable=False)
        self.pill_work.clicked.connect(lambda: self.apply_scene("work"))
        self.pill_work.rightClicked.connect(lambda: self.show_preset_context_menu("work", self.pill_work))

        self.pill_night = ToggleChip(text=t("preset_night"), icon_symbol="🌙", parent=self.card, is_checkable=False)
        self.pill_night.clicked.connect(lambda: self.apply_scene("night"))
        self.pill_night.rightClicked.connect(lambda: self.show_preset_context_menu("night", self.pill_night))

        self.pill_sleep = ToggleChip(text=t("preset_sleep"), icon_symbol="🛌", parent=self.card, is_checkable=False)
        self.pill_sleep.clicked.connect(lambda: self.apply_scene("sleep"))
        self.pill_sleep.rightClicked.connect(lambda: self.show_preset_context_menu("sleep", self.pill_sleep))

        scene_layout_1.addWidget(self.pill_work)
        scene_layout_1.addWidget(self.pill_night)
        scene_layout_1.addWidget(self.pill_sleep)
        presets_section.addLayout(scene_layout_1)
        presets_section.addSpacing(8)

        # 第二行预设：午间休息、自定义 1、自定义 2
        scene_layout_2 = QHBoxLayout()
        scene_layout_2.setSpacing(10)

        self.pill_noon = ToggleChip(text=t("preset_noon"), icon_symbol="☕", parent=self.card, is_checkable=False)
        self.pill_noon.clicked.connect(lambda: self.apply_scene("noon"))
        self.pill_noon.rightClicked.connect(lambda: self.show_preset_context_menu("noon", self.pill_noon))

        self.pill_custom1 = ToggleChip(text=t("preset_custom1"), icon_symbol="🎨", parent=self.card, is_checkable=False)
        self.pill_custom1.clicked.connect(lambda: self.apply_scene("custom_1"))
        self.pill_custom1.rightClicked.connect(lambda: self.show_preset_context_menu("custom_1", self.pill_custom1))

        self.pill_custom2 = ToggleChip(text=t("preset_custom2"), icon_symbol="🌟", parent=self.card, is_checkable=False)
        self.pill_custom2.clicked.connect(lambda: self.apply_scene("custom_2"))
        self.pill_custom2.rightClicked.connect(lambda: self.show_preset_context_menu("custom_2", self.pill_custom2))

        scene_layout_2.addWidget(self.pill_noon)
        scene_layout_2.addWidget(self.pill_custom1)
        scene_layout_2.addWidget(self.pill_custom2)
        presets_section.addLayout(scene_layout_2)

        card_layout.addLayout(presets_section)
        card_layout.addStretch(1)

        # -------------------------------------------------------------
        # 5. 一键黑屏挂机磁贴 (StealthActionCard 双行精雕排版，对标网页端)
        # -------------------------------------------------------------
        self.btn_stealth = StealthActionCard(self.card)
        self.btn_stealth.clicked.connect(self.trigger_stealth_mode)
        card_layout.addWidget(self.btn_stealth)

        root_layout.addWidget(self.card)
        self.apply_theme(self.current_theme, is_initial=True)
        self._update_preset_pills()

    def _load_initial_state(self):
        """从引擎和配置加载初始状态 (首次启动继承真实屏幕物理亮度，下次启动显示上次保存的亮度)"""
        initial_b = self.engine.current_brightness
        initial_w = self.engine.current_warmth
        initial_2x = self.engine.enhanced_2x

        self.brightness_slider.setValue(initial_b)
        self.warmth_slider.setValue(initial_w)
        self.chip_2x.setChecked(initial_2x)
        if hasattr(self, "chip_warmth") and self.chip_warmth:
            self.chip_warmth.blockSignals(True)
            self.chip_warmth.setChecked(initial_w > 5)
            self.chip_warmth.blockSignals(False)

        # 若加载已保存的极暗设置，确保遮罩同步生效
        if self.engine.overlay_opacity > 0.0 and not self.is_stealth_mode:
            self.overlay.set_target_opacity(self.engine.overlay_opacity)

        self.luminary.set_state(brightness=initial_b, warmth=initial_w)
        self._update_status_display(initial_b)
        self.update_multi_monitor_sensing()

    def eventFilter(self, obj, event):
        """监听全局鼠标移动与键盘按键事件 (附带模态与偏好设置子窗口保护)"""
        if getattr(self, "is_stealth_mode", False):
            # 保护偏好设置与子弹窗：如果正在显示设置对话框，绝不拦截子窗口任何交互事件
            if hasattr(self, "_settings_dialog") and self._settings_dialog and self._settings_dialog.isVisible():
                return super().eventFilter(obj, event)
            if event.type() in (QEvent.KeyPress, QEvent.MouseButtonPress):
                self.wake_up_from_stealth()
                return True
            elif event.type() == QEvent.MouseMove:
                # 忽略细微静止漂移，触发防刺眼柔和苏醒
                self.wake_up_from_stealth()
                return False
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        """窗口显示时，自动将键盘焦点导向主亮度滑块，使用户可以直接使用左右方向键 1% 微调"""
        super().showEvent(event)
        # 注意：杜绝调用 SetWindowCompositionAttribute 导致全屏直角黑框，交由 Qt WA_TranslucentBackground 纯净渲染
        if hasattr(self, "brightness_slider") and self.brightness_slider:
            self.brightness_slider.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        """键盘方向键精细调节：← / → 键 1% 步进调节亮度，Shift + 方向键 5% 步进"""
        key = event.key()
        modifiers = event.modifiers()
        step = 5 if (modifiers & Qt.ShiftModifier) else 1

        if key in (Qt.Key_Left, Qt.Key_Down):
            self.adjust_brightness(-step)
            event.accept()
            return
        elif key in (Qt.Key_Right, Qt.Key_Up):
            self.adjust_brightness(+step)
            event.accept()
            return
        elif key == Qt.Key_PageDown:
            self.adjust_brightness(-10)
            event.accept()
            return
        elif key == Qt.Key_PageUp:
            self.adjust_brightness(+10)
            event.accept()
            return
        elif key == Qt.Key_Home:
            self.set_brightness(1)
            event.accept()
            return
        elif key == Qt.Key_End:
            self.set_brightness(100)
            event.accept()
            return
        elif key == Qt.Key_Escape:
            # 极暗或挂机状态下，按 Esc 视为紧急脱困：还原为系统默认状态
            if self.is_stealth_mode or self.engine.current_brightness <= 10:
                self.reset_to_system_default()
            else:
                self.hide()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """关闭窗口时清理事件过滤器"""
        qapp = QApplication.instance()
        if qapp:
            try:
                qapp.removeEventFilter(self)
            except Exception:
                pass
        super().closeEvent(event)

    # -------------------------------------------------------------
    # 状态调节与核心引擎联动
    # -------------------------------------------------------------
    def set_brightness(self, value: int):
        """调节亮度并联动引擎与遮罩"""
        hw, ov = self.engine.set_brightness(value)
        if self.brightness_slider.value() != value:
            self.brightness_slider.setValue(value)

        # 若未处于纯黑挂机模式，更新遮罩透明度
        if not self.is_stealth_mode:
            self.overlay.set_target_opacity(ov)

        self.luminary.set_state(
            brightness=value,
            warmth=self.engine.current_warmth,
            is_sleep=self.is_stealth_mode or value < 20,
        )
        self._update_status_display(value)
        self.state_changed.emit()

    def _on_chip_warmth_toggled(self, checked: bool):
        """点击【🌙 舒缓防蓝光】微芯片，一键切换防蓝光护眼模式"""
        if checked:
            if self.engine.current_warmth <= 5:
                self.set_warmth(50)
        else:
            if self.engine.current_warmth > 0:
                self.set_warmth(0)

    def set_warmth(self, value: int):
        """调节琥珀色温"""
        self.engine.set_warmth(value)
        if self.warmth_slider.value() != value:
            self.warmth_slider.setValue(value)

        # 联动【🌙 舒缓防蓝光】微芯片高亮状态
        if hasattr(self, "chip_warmth") and self.chip_warmth:
            self.chip_warmth.blockSignals(True)
            self.chip_warmth.setChecked(value > 5)
            self.chip_warmth.blockSignals(False)

        self.luminary.set_state(
            brightness=self.engine.current_brightness,
            warmth=value,
            is_sleep=self.is_stealth_mode or self.engine.current_brightness < 20,
        )
        self.state_changed.emit()

    def set_enhanced_2x(self, enabled: bool):
        """切换 2x 深度压暗微芯片"""
        if self.chip_2x.isChecked() != enabled:
            self.chip_2x.setChecked(enabled)

        hw, ov = self.engine.set_enhanced_2x(enabled)
        if not self.is_stealth_mode:
            self.overlay.set_target_opacity(ov)

        self.luminary.set_state(
            brightness=self.engine.current_brightness,
            warmth=self.engine.current_warmth,
            is_sleep=self.is_stealth_mode or self.engine.current_brightness < 20,
        )
        self.config.set("enhanced_2x", enabled)
        self._update_status_display(self.engine.current_brightness)

    def adjust_brightness(self, delta: int):
        """通过快捷键步进调节亮度"""
        new_val = max(1, min(100, self.engine.current_brightness + delta))
        self.set_brightness(new_val)
        if hasattr(self, "hud") and self.hud:
            self.hud.show_value(new_val, "brightness")

    def apply_scene(self, scene_name: str):
        """应用预设情境（支持全部 6 大情境的用户自定义读取与执行）"""
        if getattr(self, "is_stealth_mode", False):
            self.wake_up_from_stealth()

        self.current_scene_key = scene_name

        presets = self.config.get_scene_presets()
        p_data = presets.get(scene_name) or DEFAULT_SCENE_PRESETS.get(scene_name, {})

        b = int(p_data.get("brightness", 50))
        w = int(p_data.get("warmth", 0))
        boost = bool(p_data.get("boost_2x", False))

        self.set_enhanced_2x(boost)
        self.set_brightness(b)
        self.set_warmth(w)
        self._update_preset_pills()

    def open_preset_customizer(self, initial_preset_key: Optional[str] = None):
        """打开常用场景预设可视化自定义与管理中心（优先选中当前正在生效的场景）"""
        if initial_preset_key is None:
            initial_preset_key = getattr(self, "current_scene_key", "work") or "work"
        from src.widgets.preset_dialog import PresetCustomizerDialog
        dlg = PresetCustomizerDialog(
            config=self.config,
            engine=self.engine,
            parent=self,
            initial_preset_key=initial_preset_key,
        )
        dlg.exec_()

    def show_preset_context_menu(self, preset_key: str, pill_widget: QWidget):
        """右键弹出 macOS 原生质感预设管理菜单"""
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        cur_th = getattr(self, "current_theme", "dark")
        if cur_th == "light":
            menu.setStyleSheet("""
                QMenu {
                    background: rgba(255, 255, 255, 0.98);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 8px;
                    padding: 4px;
                    font-size: 12px;
                    color: #0F172A;
                }
                QMenu::item {
                    padding: 6px 18px 6px 12px;
                    border-radius: 6px;
                }
                QMenu::item:selected {
                    background: rgba(245, 179, 56, 0.20);
                    color: #B45309;
                }
                QMenu::separator {
                    height: 1px;
                    background: rgba(0, 0, 0, 0.08);
                    margin: 4px 6px;
                }
            """)
        elif cur_th == "liquid_glass":
            menu.setStyleSheet("""
                QMenu {
                    background: rgba(15, 23, 42, 0.96);
                    border: 1px solid rgba(56, 189, 248, 0.35);
                    border-radius: 8px;
                    padding: 4px;
                    font-size: 12px;
                    color: #F8FAFC;
                }
                QMenu::item {
                    padding: 6px 18px 6px 12px;
                    border-radius: 6px;
                }
                QMenu::item:selected {
                    background: rgba(56, 189, 248, 0.25);
                    color: #38BDF8;
                }
                QMenu::separator {
                    height: 1px;
                    background: rgba(255, 255, 255, 0.10);
                    margin: 4px 6px;
                }
            """)
        else:
            menu.setStyleSheet("""
                QMenu {
                    background: rgba(24, 26, 32, 0.98);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 8px;
                    padding: 4px;
                    font-size: 12px;
                    color: #F1F5F9;
                }
                QMenu::item {
                    padding: 6px 18px 6px 12px;
                    border-radius: 6px;
                }
                QMenu::item:selected {
                    background: rgba(245, 179, 56, 0.25);
                    color: #F5B338;
                }
                QMenu::separator {
                    height: 1px;
                    background: rgba(255, 255, 255, 0.08);
                    margin: 4px 6px;
                }
            """)

        presets = self.config.get_scene_presets()
        p_data = presets.get(preset_key) or DEFAULT_SCENE_PRESETS.get(preset_key, {})
        name = self._preset_display_name(preset_key, p_data)

        act_apply = menu.addAction(t("preset_menu_apply", "⚡ 立即应用「{name}」").format(name=name))
        act_apply.triggered.connect(lambda: self.apply_scene(preset_key))

        act_save_curr = menu.addAction(t("preset_menu_save", "📍 将当前屏幕参数覆盖保存至此预设"))
        act_save_curr.triggered.connect(lambda: self.save_current_to_preset(preset_key))

        menu.addSeparator()

        act_edit = menu.addAction(t("preset_menu_edit", "✏️ 自定义参数与名称..."))
        act_edit.triggered.connect(lambda: self.open_preset_customizer(preset_key))

        act_reset = menu.addAction(t("preset_menu_reset", "↺ 恢复此预设默认值"))
        act_reset.triggered.connect(lambda: self.reset_preset_default(preset_key))

        menu.exec_(QCursor.pos())
        menu.deleteLater()

    def save_current_to_preset(self, preset_key: str):
        """将当前屏幕参数快速覆盖保存至指定预设"""
        presets = self.config.get_scene_presets()
        p_data = presets.get(preset_key) or DEFAULT_SCENE_PRESETS.get(preset_key, {})
        name = p_data.get("name", preset_key)
        icon = p_data.get("icon", "")

        presets[preset_key] = {
            "name": name,
            "icon": icon,
            "brightness": self.engine.current_brightness,
            "warmth": self.engine.current_warmth,
            "boost_2x": bool(getattr(self.engine, "enhanced_2x", False)),
        }
        self.config.set_scene_presets(presets)
        self.config.save()
        self._update_preset_pills()
        self._notify_status(t("preset_saved_toast", "✓ 已保存至当前预设"))

    def reset_preset_default(self, preset_key: str):
        """恢复指定预设的出厂默认值"""
        if preset_key not in DEFAULT_SCENE_PRESETS:
            return
        presets = self.config.get_scene_presets()
        presets[preset_key] = copy.deepcopy(DEFAULT_SCENE_PRESETS[preset_key])
        self.config.set_scene_presets(presets)
        self.config.save()
        self._update_preset_pills()
        self._notify_status(t("preset_restored_toast", "✓ 该预设已恢复出厂默认值"))

    @staticmethod
    def _preset_display_name(key: str, data: Dict[str, Any]) -> str:
        """
        计算预设的展示名称：
        - 用户改过名字（与出厂名不同）→ 尊重用户自定义名称；
        - 仍是出厂名 → 使用当前界面语言的内置名称，避免英文界面里冒出中文预设名。
        """
        stored_name = str(data.get("name", "") or "")
        factory_name = str(DEFAULT_SCENE_PRESETS.get(key, {}).get("name", ""))
        if stored_name and stored_name != factory_name:
            return stored_name
        return t(f"preset_name_{key}") or stored_name or factory_name or key

    def _update_preset_pills(self):
        """动态根据最新配置全量刷新 6 大情境微芯片的显示文本与悬浮提示"""
        presets = self.config.get_scene_presets()

        pills = {
            "work": getattr(self, "pill_work", None),
            "night": getattr(self, "pill_night", None),
            "sleep": getattr(self, "pill_sleep", None),
            "noon": getattr(self, "pill_noon", None),
            "custom_1": getattr(self, "pill_custom1", None),
            "custom_2": getattr(self, "pill_custom2", None),
        }

        for key, pill in pills.items():
            if not pill:
                continue
            data = presets.get(key) or DEFAULT_SCENE_PRESETS.get(key, {})
            name = self._preset_display_name(key, data)
            icon = data.get("icon", "")
            b = data.get("brightness", 50)
            w = data.get("warmth", 0)
            boost = data.get("boost_2x", False)

            # 更新药丸文本：显示场景名称与当前亮度进度 (例如：白天办公 90%)
            if icon:
                pill.setIconSymbol(icon)
            pill.setText(f"{name} {b}%")

            boost_tag = t("preset_boost_tag", " · 深度压暗") if boost else ""
            hint = t("preset_save_hint", "左键单击：应用预设\n右键单击：自定义参数或覆盖保存")
            pill.setToolTip(
                f"{icon} {name} ({b}% {t('brightness')} / {w}% {t('warmth')}{boost_tag})\n{hint}"
            )

    def _check_stealth_mouse_wiggle(self):
        """挂机期间全局光标位移检测：晃动鼠标即时平滑苏醒（无须侵入式钩子）"""
        if not self.is_stealth_mode:
            if hasattr(self, "_stealth_poll_timer"):
                self._stealth_poll_timer.stop()
            return
        import time
        if time.time() - getattr(self, "_stealth_start_time", 0.0) < 0.35:
            self._stealth_mouse_start_pos = QCursor.pos()
            return
        if self._stealth_mouse_start_pos is None:
            self._stealth_mouse_start_pos = QCursor.pos()
            return
        current_pos = QCursor.pos()
        dx = current_pos.x() - self._stealth_mouse_start_pos.x()
        dy = current_pos.y() - self._stealth_mouse_start_pos.y()
        if (dx * dx + dy * dy) >= 400:  # 20px 阈值防静止微颤
            self.wake_up_from_stealth()

    def trigger_stealth_mode(self):
        """进入睡前纯黑挂机沉浸模式 (99.5% 极限遮罩，听歌挂机不刺眼)"""
        if getattr(self, "is_stealth_mode", False):
            return
        import time
        self.is_stealth_mode = True
        self._stealth_start_time = time.time()
        self._stealth_mouse_start_pos = QCursor.pos()
        if hasattr(self, "_stealth_poll_timer"):
            self._stealth_poll_timer.start(50)
        qapp = QApplication.instance()
        if qapp:
            qapp.installEventFilter(self)
        self.overlay.trigger_stealth_mode(0.995)
        self.luminary.set_state(
            brightness=1,
            warmth=self.engine.current_warmth,
            is_sleep=True,
        )
        self.lbl_status.setText(f"{t('stealth_title')} {t('stealth_sub')}")

    def wake_up_from_stealth(self):
        """从纯黑挂机状态通过三次贝塞尔曲线平滑柔和苏醒"""
        if not self.is_stealth_mode:
            return
        self.is_stealth_mode = False
        if hasattr(self, "_stealth_poll_timer"):
            self._stealth_poll_timer.stop()
        self._stealth_mouse_start_pos = None
        qapp = QApplication.instance()
        if qapp:
            try:
                qapp.removeEventFilter(self)
            except Exception:
                pass
        target_ov = self.engine.overlay_opacity
        duration = 1500 if self.config.get("smooth_wake", True) else 0
        if duration > 0:
            self.overlay.wake_up_with_bezier(target_opacity=target_ov)
        else:
            # 用户关闭「平滑苏醒」时立即恢复，不做贝塞尔渐亮
            self.overlay.set_target_opacity(target_ov, animate=False)
        self.luminary.set_state(
            brightness=self.engine.current_brightness,
            warmth=self.engine.current_warmth,
            is_sleep=self.engine.current_brightness < 20,
        )
        self._update_status_display(self.engine.current_brightness)
        self.state_changed.emit()

    @staticmethod
    def _display_target_label(target_idx: Optional[int]) -> str:
        """把调光作用域翻译为当前语言的徽标文本（多屏徽标文案不再由 core 层硬编码中文）"""
        if target_idx is None:
            return t("display_sync")
        if target_idx == 0:
            return t("display_primary")
        return t("display_secondary").format(n=target_idx + 1)

    def _on_multi_monitor_clicked(self):
        """用户点击多屏拓扑胶囊时，循环切换调光作用域并在屏幕中央浮现灵动 HUD 回执"""
        target_idx, _label = self.engine.cycle_display_target()
        label = self._display_target_label(target_idx)
        self.multi_monitor_badge.setText(label)

        # 交由引擎统一做状态对齐（重算双轨层级），绝不在 UI 层直接改 engine.current_brightness
        current_b = self.engine.sync_from_display(target_idx)

        self.brightness_slider.blockSignals(True)
        self.brightness_slider.setValue(current_b)
        self.brightness_slider.blockSignals(False)

        self.luminary.set_state(brightness=current_b, warmth=self.engine.current_warmth)
        self._update_status_display(current_b)
        self.state_changed.emit()
        if hasattr(self, "hud") and self.hud:
            self.hud.show_notice(label, f"{current_b}%")

    def update_multi_monitor_sensing(self, screen_count: Optional[int] = None):
        """智能多屏幕感知：多显示器时显示同步徽标，单显示器彻底隐藏"""
        if screen_count is None:
            screens = QApplication.screens()
            screen_count = len(screens) if screens else 1
        self.multi_monitor_badge.setVisible(screen_count > 1)

    def _update_reset_button_affordance(self, is_low_light: bool = False):
        """低光人机安全可视增强：当亮度极低 (<=10%) 时赋予一键恢复原状按钮金琥珀微光与脱困 Tooltip"""
        if not hasattr(self, "btn_reset") or not self.btn_reset:
            return
        if is_low_light:
            self.btn_reset.setStyleSheet("""
                QPushButton {
                    background: rgba(245, 179, 56, 0.22);
                    border: 1.5px solid #F5B338;
                    border-radius: 12px;
                    color: #FBBF24;
                    font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 13px;
                    font-weight: 700;
                    padding: 2px 12px;
                }
                QPushButton:hover {
                    background: rgba(245, 179, 56, 0.35);
                    border-color: #FCD34D;
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(245, 179, 56, 0.45);
                }
            """)
            self.btn_reset.setToolTip(t("reset_emergency_tooltip", "太暗看不清？点击这里立即恢复系统原状 (或按 Ctrl+Alt+Backspace 紧急唤醒)"))
        else:
            cur_th = getattr(self, "current_theme", "dark")
            if cur_th == "light":
                self.btn_reset.setStyleSheet("""
                    QPushButton {
                        background: rgba(0, 0, 0, 0.04);
                        border: 1px solid rgba(0, 0, 0, 0.08);
                        border-radius: 12px;
                        color: #1D1D1F;
                        font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 12.5px;
                        font-weight: 600;
                        padding: 2px 12px;
                    }
                    QPushButton:hover {
                        background: rgba(0, 0, 0, 0.08);
                        border-color: rgba(0, 0, 0, 0.16);
                        color: #1D1D1F;
                    }
                    QPushButton:pressed {
                        background: rgba(0, 0, 0, 0.14);
                    }
                """)
            elif cur_th == "liquid_glass":
                self.btn_reset.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.10);
                        border: 1px solid rgba(255, 255, 255, 0.18);
                        border-top: 1px solid rgba(255, 255, 255, 0.45);
                        border-radius: 12px;
                        color: #FFFFFF;
                        font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 12.5px;
                        font-weight: 600;
                        padding: 2px 12px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.20);
                        border-color: rgba(255, 255, 255, 0.35);
                        color: #FFFFFF;
                    }
                    QPushButton:pressed {
                        background: rgba(255, 255, 255, 0.28);
                    }
                """)
            else:
                self.btn_reset.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.06);
                        border: 1px solid rgba(255, 255, 255, 0.10);
                        border-radius: 12px;
                        color: rgba(235, 235, 245, 0.85);
                        font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 12.5px;
                        font-weight: 600;
                        padding: 2px 12px;
                    }
                    QPushButton:hover {
                        background: rgba(245, 179, 56, 0.18);
                        border-color: rgba(245, 179, 56, 0.48);
                        color: #F5B338;
                    }
                    QPushButton:pressed {
                        background: rgba(255, 255, 255, 0.18);
                    }
                """)
            self.btn_reset.setToolTip(t("reset_tooltip"))

    def _update_status_display(self, brightness: int):
        """更新顶部状态描述文本与低光人机安全脱困引导 (根据当前语言环境动态呈现)"""
        is_low = (brightness <= 10) or (hasattr(self, "chip_2x") and self.chip_2x.isChecked() and brightness <= 15)
        self._update_reset_button_affordance(is_low)

        if self.is_stealth_mode:
            self.lbl_status.setText(f"{t('stealth_title')} {t('stealth_sub')}")
        elif is_low:
            self.lbl_status.setText(t("status_sleep_hint", "🛌 助眠微光中 (按 Esc 或 Ctrl+Alt+Backspace 还原)"))
        elif brightness < 20 or (self.chip_2x.isChecked() and brightness < 30):
            self.lbl_status.setText(t("status_sleep"))
        elif brightness > 70:
            self.lbl_status.setText(t("status_day"))
        else:
            self.lbl_status.setText(t("status_night"))

    def _notify_status(self, message: str, duration_ms: int = 2500):
        """在主面板状态行短暂呈现一条操作回执，随后自动恢复常规状态文案"""
        try:
            self.lbl_status.setText(message)
            QTimer.singleShot(duration_ms, lambda: self._update_status_display(self.engine.current_brightness))
        except Exception:
            pass

    def retranslate_ui(self, lang: Optional[str] = None):
        """全界面动态多语言重绘 (无需重启客户端)"""
        if lang:
            set_language(lang)
        cur_lang = get_language()
        self.setWindowTitle(t("app_full_title"))
        self.lbl_title.setText(t("app_title"))
        self._update_status_display(self.engine.current_brightness)
        self.multi_monitor_badge.setText(self._display_target_label(getattr(self.engine, "target_display", None)))
        self.btn_reset.setText(t("reset"))
        self.btn_reset.setToolTip(t("reset_tooltip"))
        self.btn_settings.setToolTip(t("settings_tooltip"))
        self.btn_minimize.setToolTip(t("min_tooltip"))
        self.btn_close.setToolTip(t("close_tooltip"))
        self.lbl_bright_title.setText(t("brightness"))
        self.chip_2x.setText(t("boost_2x"))
        self.chip_warmth.setText(t("warmth_chip"))
        self.lbl_warmth_title.setText(t("warmth"))
        self.lbl_presets_title.setText(t("presets_title"))
        self.btn_manage_presets.setText(t("manage_presets"))
        self.btn_theme_toggle.setText(
            {"dark": t("theme_dark"), "light": t("theme_light"), "liquid_glass": t("theme_liquid_glass")}.get(
                getattr(self, "current_theme", "dark"), t("theme_dark")
            )
        )
        self._update_preset_pills()
        if hasattr(self, "btn_stealth") and self.btn_stealth:
            self.btn_stealth.update()
        self.brightness_slider.setTitle(t("brightness"))
        self.warmth_slider.setTitle(t("warmth"))
        self.language_changed.emit(cur_lang)

    # -------------------------------------------------------------
    # 窗口交互与拖拽停靠
    # -------------------------------------------------------------
    def mousePressEvent(self, event):
        """无边框窗口拖动支持"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        if self.config.get("remember_window_position", True):
            self.config.set("window_pos", [self.x(), self.y()])
            self.config.save()

    def moveEvent(self, event):
        """无论通过鼠标拖拽还是系统 Snap 贴边，实时追踪主面板最新物理停靠坐标"""
        super().moveEvent(event)
        if hasattr(self, "config") and self.isVisible():
            if self.config.get("remember_window_position", True):
                self.config.set("window_pos", [self.x(), self.y()])

    def position_center_screen(self):
        """将主面板优雅居中呈现在主屏幕黄金分割位置（居中靠上），符合初次双击启动的人机工程学"""
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            x = avail.x() + (avail.width() - self.width()) // 2
            y = avail.y() + int((avail.height() - self.height()) * 0.42)
            self.move(max(avail.x(), x), max(avail.y(), y))

    def toggle_panel(self, force_show: Optional[bool] = None, from_tray: bool = False):
        """呼出或隐藏主控制中心面板：支持记忆窗口上次拖拽位置与右下角托盘停靠"""
        if force_show is True:
            should_show = True
        elif force_show is False:
            should_show = False
        else:
            if from_tray and self.isVisible() and not self.isActiveWindow():
                should_show = True
            else:
                should_show = not self.isVisible()

        if should_show:
            from src.win32_compat import is_fullscreen_window_active
            if not from_tray and not force_show and self.config.get("fullscreen_guard", True) and is_fullscreen_window_active():
                if hasattr(self, "hud") and self.hud:
                    self.hud.show_notice(t("app_title"), f"{self.engine.current_brightness}%")
                return
            remember = self.config.get("remember_window_position", True)
            last_pos = self.config.get("window_pos", None)
            restored = False

            if remember and last_pos and isinstance(last_pos, (list, tuple)) and len(last_pos) == 2:
                target_pt = QPoint(int(last_pos[0]), int(last_pos[1]))
                screen = QApplication.screenAt(target_pt) or QApplication.primaryScreen()
                if screen:
                    avail = screen.availableGeometry()
                    clamped_x = max(avail.x(), min(target_pt.x(), avail.right() - self.width() + 40))
                    clamped_y = max(avail.y(), min(target_pt.y(), avail.bottom() - self.height() + 40))
                    self.move(clamped_x, clamped_y)
                    restored = True

            if not restored:
                if from_tray or remember:
                    self.reposition_near_tray()
                elif not self.isVisible():
                    self.position_center_screen()
                if remember:
                    self.config.set("window_pos", [self.x(), self.y()])
                    self.config.save()

            self.show()
            self.raise_()
            self.activateWindow()
        else:
            if self.config.get("remember_window_position", True):
                self.config.set("window_pos", [self.x(), self.y()])
                self.config.save()
            self.hide()

    # -------------------------------------------------------------
    # 全局快捷键（动作 → 回调 的唯一真相源）
    # -------------------------------------------------------------
    def _hotkey_callbacks(self) -> Dict[str, Callable[[], None]]:
        """
        返回「配置动作键 → 回调」映射表。**全项目唯一一份**。

        回调本身运行在 Win32 热键消息泵线程，因此统一经 `GuiDispatcher.post`
        排队回 Qt 主事件循环执行，杜绝跨线程操作控件。

        新增热键动作时：在此表登记即可，`src/main.py` 会自动拾取。
        """
        def dispatch(func: Callable[[], None]) -> Callable[[], None]:
            return lambda: self._gui_dispatcher.post(func)

        return {
            "brightness_up": dispatch(lambda: self.adjust_brightness(+5)),
            "brightness_down": dispatch(lambda: self.adjust_brightness(-5)),
            "toggle_sleep": dispatch(lambda: self.apply_scene("sleep")),
            "toggle_stealth": dispatch(self.trigger_stealth_mode),
            "toggle_spotlight": dispatch(self.toggle_spotlight),
            "panic_restore": dispatch(self.emergency_restore),
            "toggle_panel": dispatch(self.toggle_panel),
            "open_settings": dispatch(self.open_settings),
        }

    def register_all_hotkeys(self) -> bool:
        """
        按当前配置注册全部全局快捷键（启动时与设置改动后共用同一入口）。

        :return: 是否全部注册成功。任一动作注册失败（如被系统占用）返回 False，
                 调用方可据此回滚配置，避免「配置写入了、运行时却没生效」。
        """
        if not self.hotkey_mgr:
            return True
        hk_dict = self.config.get_hotkeys()
        all_ok = True
        logger = logging.getLogger("LunaGui")
        for action, callback in self._hotkey_callbacks().items():
            key = hk_dict.get(action)
            if not key:
                continue
            try:
                if not self.hotkey_mgr.register_hotkey(action, key, callback):
                    all_ok = False
                    logger.warning("全局快捷键注册失败（可能被占用）: %s -> %s", action, key)
            except Exception:
                all_ok = False
                logger.exception("注册全局快捷键异常: %s", action)
        return all_ok

    def reload_hotkeys(self) -> bool:
        """热重载全局快捷键（设置页录制新键位、恢复默认后调用）"""
        return self.register_all_hotkeys()

    def emergency_restore(self) -> None:
        """急救逃生：恢复满光中性状态，并把主面板居中弹到眼前给予安全反馈"""
        self.reset_to_system_default()
        self.position_center_screen()
        self.show()
        self.raise_()
        self.activateWindow()

    def reposition_near_tray(self, tray_geometry=None):
        """将主面板精准智能停靠在右下角系统托盘正上方 (多显示器光标屏幕自动识别)"""
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            margin = 12
            x = avail.x() + avail.width() - self.width() - margin
            y = avail.y() + avail.height() - self.height() - margin
            self.move(x, y)

    def reset_to_system_default(self):
        """一键重置：将屏幕亮度和色温恢复为系统初始原貌（100% 满光、0 护眼色温、完全清除软件遮罩）"""
        target_b = 100
        
        # 退出纯黑挂机模式（若处于挂机状态）
        if self.is_stealth_mode:
            self.wake_up_from_stealth()

        # 1. 重置 2x 深度压暗芯片
        if self.chip_2x.isChecked():
            self.chip_2x.setChecked(False)
        self.set_enhanced_2x(False)

        # 2. 重置色温为 0 (完全恢复原始色彩中性白平衡)
        self.warmth_slider.setValue(0)
        self.set_warmth(0)

        # 3. 恢复亮度为 100% 满光并清除所有遮罩
        self.brightness_slider.setValue(target_b)
        self.set_brightness(target_b)

        # 4. 确保底层遮罩完全清零透明
        if hasattr(self.overlay, "set_target_opacity"):
            self.overlay.set_target_opacity(0.0)

        # 5. 更新配置保存
        self.config.set("brightness", target_b)
        self.config.set("warmth", 0)
        self.config.set("enhanced_2x", False)
        self.config.save()

        # 6. 状态反馈与联动广播 (简短明晰，杜绝换行挤压截断)
        self.current_scene_key = "work"
        self._update_preset_pills()
        self.lbl_status.setText(t("reset_done", "✓ 已恢复默认原状"))
        self.state_changed.emit()
        QTimer.singleShot(2500, lambda: self._update_status_display(target_b))

    def exit_app(self):
        """安全退出程序并恢复系统原始物理亮度与色温"""
        if self.engine:
            self.engine.restore_on_exit()
        QApplication.instance().quit()

    def brightness_up(self, step: int = 5):
        """亮度步进递增"""
        self.adjust_brightness(step)

    def brightness_down(self, step: int = 5):
        """亮度步进递减"""
        self.adjust_brightness(-step)

    def toggle_sleep(self):
        """切换助眠极暗场景"""
        self.apply_scene("sleep")

    def toggle_stealth(self):
        """切换纯黑挂机模式"""
        self.trigger_stealth_mode()

    def panic_restore(self):
        """急救防刺眼：瞬间还原系统原生默认状态"""
        self.reset_to_system_default()

    def check_for_updates(self, silent: bool = False):
        """由主窗口发起后台版本检测 (供托盘菜单与开机自启调用)"""
        worker = getattr(self, "_main_update_worker", None)
        if worker is not None and worker.isRunning():
            # 已有检测在飞行中：不重复创建 QThread，避免线程对象被提前回收
            return
        self._main_update_worker = UpdateWorker(parent=self)
        self._main_update_worker.sig_finished.connect(
            lambda ok, data, err: self._on_main_update_finished(ok, data, err, silent),
            Qt.QueuedConnection,
        )
        self._main_update_worker.start()

    def _on_main_update_finished(self, success: bool, data: dict, error_msg: str, silent: bool):
        worker = getattr(self, "_main_update_worker", None)
        if worker is not None:
            worker.deleteLater()
            self._main_update_worker = None
        if success and data:
            remote_ver = data.get("version", "")
            if is_newer_version(remote_ver, CURRENT_VERSION):
                self._cached_update_data = data
                # 遵循用户哲学：首页绝不弹窗、绝不提示、绝不显示药丸，完全保持首页纯净零打扰
                # 仅将更新数据留存，供用户自主打开「软件偏好设置」时在侧边栏条目与版本行呈现红点
                if hasattr(self, "btn_update_pill"):
                    self.btn_update_pill.setVisible(False)
            elif not silent:
                # 仅在非静默检测且没有更新时在状态栏微提示当前版本
                self._notify_status(f"{t('update_latest')} (v{CURRENT_VERSION})")
        elif not silent:
            self._notify_status(t("update_failed"))

    def _on_update_pill_clicked(self):
        """用户主动点击首页更新小药丸时，唤起升级详情"""
        if hasattr(self, "_cached_update_data") and self._cached_update_data:
            dialog = UpgradeDialog(update_info=self._cached_update_data, parent=self)
            result = dialog.exec_()
            if result != QDialog.Accepted:
                self._dismissed_update_version = self._cached_update_data.get("version", "")

    def _on_screens_changed(self, screen=None):
        """当外接显示器热插拔 (HDMI / Type-C) 时，毫秒级自适应多屏幕拓扑并刷新遮罩几何"""
        screens = QApplication.screens()
        count = len(screens) if screens else 1
        self.update_multi_monitor_sensing(screen_count=count)
        if hasattr(self, "overlay") and self.overlay:
            self.overlay.refresh_geometry()
        # 拓扑变化后双轨层级可能失效（例如从双屏退回单屏），重新对齐当前目标显示器
        if count <= 1:
            self.engine.target_display = None

    def toggle_spotlight(self):
        """开启 / 关闭暗夜微光聚光灯透视 (光标周围局部柔和照亮)"""
        self._spotlight_active = not self._spotlight_active
        if self._spotlight_active:
            self._spotlight_timer.start(30)
            self._update_spotlight_pos()
            if hasattr(self, "hud") and self.hud:
                self.hud.show_notice(t("hud_spotlight_on", "🔦 微光聚光灯 开启"), "")
        else:
            self._spotlight_timer.stop()
            if hasattr(self, "overlay") and self.overlay:
                self.overlay.set_flashlight_pos(None)
            if hasattr(self, "hud") and self.hud:
                self.hud.show_notice(t("hud_spotlight_off", "🔦 微光聚光灯 关闭"), "")
        self.state_changed.emit()

    def _update_spotlight_pos(self):
        if not getattr(self, "_spotlight_active", False):
            return
        if hasattr(self, "overlay") and self.overlay:
            pos = QCursor.pos()
            ov_pos = self.overlay.mapFromGlobal(pos)
            self.overlay.set_flashlight_pos(ov_pos)

    def open_sponsor_dialog(self):
        """唤出开发者赞赏与夜深守候心意对话框"""
        from src.sponsor_dialog import SponsorDialog
        dlg = SponsorDialog(parent=self)
        dlg.exec_()

    def open_feedback_dialog(self):
        """唤出安全人机防刷反馈对话框"""
        from src.feedback_dialog import FeedbackDialog
        dlg = FeedbackDialog(parent=self)
        dlg.exec_()

    def _cycle_theme_quick(self):
        """主界面一键快捷切换主题（暗色 -> 浅色 -> 液态玻璃 -> 暗色）"""
        order = ["dark", "light", "liquid_glass"]
        cur = getattr(self, "current_theme", "dark")
        idx = order.index(cur) if cur in order else 0
        next_theme = order[(idx + 1) % len(order)]
        self.apply_theme(next_theme)
        self.config.set("theme", next_theme)
        self.config.save()

    def open_settings(self):
        """打开偏好设置对话框（单例快速复用，具备防交互卡死的多重自愈保障）"""
        logging.info("收到打开偏好设置请求，执行环境自愈与状态重置...")

        # 1. 若当前仍处于纯黑挂机模式，先平滑苏醒，防止黑屏状态锁住焦点
        if getattr(self, "is_stealth_mode", False):
            self.wake_up_from_stealth()

        # 2. 防御性自愈：强制卸载可能残留的全局事件过滤器，杜绝鼠标按下事件被静默吞噬
        qapp = QApplication.instance()
        if qapp:
            try:
                qapp.removeEventFilter(self)
            except Exception:
                pass

        # 3. 强制释放任何可能残留的鼠标捕获 (Win32 ReleaseCapture + Qt mouseGrabber)
        try:
            import ctypes
            ctypes.windll.user32.ReleaseCapture()
            grabber = QApplication.mouseGrabber()
            if grabber:
                grabber.releaseMouse()
        except Exception:
            pass

        # 4. 彻底杜绝遮罩层挡住设置弹窗：若全屏暗夜遮罩正在显示，弹窗期间暂时隐藏，杜绝休眠唤醒后全屏阻碍点击
        overlay_was_visible = False
        saved_overlay_opacity = 0.0
        if hasattr(self, "overlay") and self.overlay and self.overlay.isVisible():
            overlay_was_visible = True
            saved_overlay_opacity = self.overlay.dim_opacity
            logging.info(f"偏好设置唤起前检测到全屏遮罩处于显示状态(opacity={saved_overlay_opacity})，暂时隐藏以彻底规避点击遮挡。")
            self.overlay.hide()

        # 5. 若当前已有偏好设置窗口且正处于显示状态，直接激活置顶
        if hasattr(self, "_settings_dialog") and self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return

        # 6. 若旧实例已关闭，安全销毁并释放（记录当前停留分组），构建全新无污染对话框，彻底杜绝外链跳转后复用脏状态卡死
        if hasattr(self, "_settings_dialog") and self._settings_dialog:
            try:
                self._last_settings_nav_index = getattr(self._settings_dialog, "_current_nav_index", 0)
                self._settings_dialog.close()
                self._settings_dialog.deleteLater()
            except Exception:
                pass
            self._settings_dialog = None

        self._settings_dialog = self.create_settings_dialog()
        dialog = self._settings_dialog
        dialog.setEnabled(True)
        # 恢复用户上次停留的分组
        p_geo = self.frameGeometry()
        d_x = p_geo.x() + (p_geo.width() - dialog.width()) // 2
        d_y = p_geo.y() + (p_geo.height() - dialog.height()) // 2
        screen = QApplication.screenAt(p_geo.center()) or QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            d_x = max(avail.x() + 10, min(d_x, avail.right() - dialog.width() - 10))
            d_y = max(avail.y() + 10, min(d_y, avail.bottom() - dialog.height() - 10))
        dialog.move(d_x, d_y)
        dialog.raise_()
        dialog.activateWindow()
        logging.info("偏好设置对话框已居中弹出就绪。")
        try:
            dialog.exec_()
        finally:
            if hasattr(self, "_settings_dialog") and self._settings_dialog:
                self._last_settings_nav_index = getattr(self._settings_dialog, "_current_nav_index", 0)
                try:
                    self._settings_dialog.deleteLater()
                except Exception:
                    pass
                self._settings_dialog = None

            if overlay_was_visible and hasattr(self, "overlay") and self.overlay:
                logging.info(f"偏好设置已关闭，无缝恢复暗夜遮罩(opacity={saved_overlay_opacity})。")
                self.overlay.set_target_opacity(saved_overlay_opacity, animate=False)

    def create_settings_dialog(self) -> SettingsDialog:
        """工厂方法：创建偏好设置对话框并接入主题热联动与导航记忆"""
        dlg = SettingsDialog(config=self.config, parent=self)
        dlg.sig_theme_changed.connect(self.apply_theme)
        if hasattr(self, "_last_settings_nav_index") and isinstance(self._last_settings_nav_index, int):
            dlg._current_nav_index = self._last_settings_nav_index
            dlg._on_nav_clicked(self._last_settings_nav_index)
        return dlg

    def apply_theme(self, theme: str, is_initial: bool = False):
        """动态应用黑天 (Dark)、白夜 (Light) 与苹果液态玻璃 (Liquid Glass) 主题"""
        theme = theme if theme in ("dark", "light", "liquid_glass") else "dark"
        if not is_initial and getattr(self, "current_theme", None) == theme:
            return
        self.current_theme = theme
        if hasattr(self, "card") and self.card:
            self.card.theme = self.current_theme
            self.card.update()

        if hasattr(self, "brightness_slider") and self.brightness_slider:
            self.brightness_slider.set_theme(self.current_theme)
        if hasattr(self, "warmth_slider") and self.warmth_slider:
            self.warmth_slider.set_theme(self.current_theme)

        # 深度联动更新所有场景磁贴 (常用场景预设: 工作、暗夜、睡眠) 与特性微芯片
        for chip in (
            getattr(self, "pill_work", None),
            getattr(self, "pill_night", None),
            getattr(self, "pill_sleep", None),
            getattr(self, "pill_noon", None),
            getattr(self, "pill_custom1", None),
            getattr(self, "pill_custom2", None),
            getattr(self, "chip_2x", None),
            getattr(self, "chip_warmth", None),
            getattr(self, "multi_monitor_badge", None),
        ):
            if chip and hasattr(chip, "set_theme"):
                chip.set_theme(self.current_theme)

        if hasattr(self, "_settings_dialog") and self._settings_dialog:
            self._settings_dialog.apply_theme(self.current_theme)

        if hasattr(self, "btn_theme_toggle") and self.btn_theme_toggle:
            th_labels = {"dark": t("theme_dark"), "light": t("theme_light"), "liquid_glass": t("theme_liquid_glass")}
            self.btn_theme_toggle.setText(th_labels.get(self.current_theme, t("theme_dark")))

        if hasattr(self, "card") and self.card.graphicsEffect():
            effect = self.card.graphicsEffect()
            effect.setOffset(0, 2)
            if self.current_theme == "light":
                effect.setColor(QColor(15, 23, 42, 35))
                effect.setBlurRadius(12)
            elif self.current_theme == "liquid_glass":
                effect.setColor(QColor(15, 23, 42, 90))
                effect.setBlurRadius(12)
            else:
                effect.setColor(QColor(0, 0, 0, 120))
                effect.setBlurRadius(12)

        if self.current_theme == "light":
            # 苹果白天模式 (macOS Sonoma 纯净雪瓷白模式)
            if hasattr(self, "lbl_scale") and self.lbl_scale:
                self.lbl_scale.setVisible(False)
            if hasattr(self, "lbl_title"):
                self.lbl_title.setStyleSheet("color: #1D1D1F; font-size: 18px; font-weight: 700; border: none; background: transparent;")
            if hasattr(self, "lbl_status"):
                self.lbl_status.setStyleSheet("color: rgba(60, 60, 67, 0.75); font-size: 14px; font-weight: 500; border: none; background: transparent;")
            if hasattr(self, "lbl_bright_title"):
                self.lbl_bright_title.setStyleSheet("color: #1D1D1F; font-size: 14px; font-weight: 500;")
            if hasattr(self, "lbl_warmth_title"):
                self.lbl_warmth_title.setStyleSheet("color: #1D1D1F; font-size: 14px; font-weight: 500;")
            if hasattr(self, "lbl_presets_title"):
                self.lbl_presets_title.setStyleSheet("color: #1D1D1F; font-size: 14px; font-weight: 500;")

            cur_b = getattr(self.engine, "current_brightness", 100)
            is_low = (cur_b <= 10) or (hasattr(self, "chip_2x") and self.chip_2x.isChecked() and cur_b <= 15)
            self._update_reset_button_affordance(is_low)
            if hasattr(self, "btn_theme_toggle") and self.btn_theme_toggle:
                self.btn_theme_toggle.setStyleSheet("""
                    QPushButton {
                        background: rgba(0, 0, 0, 0.04);
                        border: 1px solid rgba(0, 0, 0, 0.08);
                        border-radius: 11px;
                        color: #1D1D1F;
                        font-size: 11.5px;
                        font-weight: 600;
                        padding: 1px 10px;
                    }
                    QPushButton:hover {
                        background: rgba(0, 0, 0, 0.08);
                        border-color: rgba(0, 0, 0, 0.16);
                        color: #1D1D1F;
                    }
                    QPushButton:pressed {
                        background: rgba(0, 0, 0, 0.14);
                    }
                """)
            if hasattr(self, "btn_manage_presets"):
                self.btn_manage_presets.setStyleSheet("""
                    QPushButton {
                        background: rgba(0, 0, 0, 0.04);
                        border: 1px solid rgba(0, 0, 0, 0.08);
                        border-radius: 12px;
                        color: #1D1D1F;
                        font-size: 12.5px;
                        font-weight: 600;
                        padding: 2px 12px;
                    }
                    QPushButton:hover {
                        background: rgba(0, 0, 0, 0.08);
                        border-color: rgba(0, 0, 0, 0.16);
                        color: #1D1D1F;
                    }
                    QPushButton:pressed {
                        background: rgba(0, 0, 0, 0.14);
                    }
                """)

            if hasattr(self, "btn_stealth") and self.btn_stealth:
                if hasattr(self.btn_stealth, "set_theme"):
                    self.btn_stealth.set_theme(self.current_theme)
        elif self.current_theme == "liquid_glass":
            # 苹果 VisionOS / macOS Sequoia 纯净高通透微晶玻璃
            if hasattr(self, "lbl_title"):
                self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 700; border: none; background: transparent;")
            if hasattr(self, "lbl_status"):
                self.lbl_status.setStyleSheet("color: rgba(235, 235, 245, 0.85); font-size: 14px; font-weight: 500; border: none; background: transparent;")
            if hasattr(self, "lbl_bright_title"):
                self.lbl_bright_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 500;")
            if hasattr(self, "lbl_warmth_title"):
                self.lbl_warmth_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 500;")
            if hasattr(self, "lbl_presets_title"):
                self.lbl_presets_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 500;")

            if hasattr(self, "lbl_scale") and self.lbl_scale:
                self.lbl_scale.setVisible(False)

            cur_b = getattr(self.engine, "current_brightness", 100)
            is_low = (cur_b <= 10) or (hasattr(self, "chip_2x") and self.chip_2x.isChecked() and cur_b <= 15)
            self._update_reset_button_affordance(is_low)

            if hasattr(self, "btn_theme_toggle") and self.btn_theme_toggle:
                self.btn_theme_toggle.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.10);
                        border: 1px solid rgba(255, 255, 255, 0.18);
                        border-top: 1px solid rgba(255, 255, 255, 0.45);
                        border-radius: 11px;
                        color: #FFFFFF;
                        font-size: 11.5px;
                        font-weight: 600;
                        padding: 1px 10px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.20);
                        border-color: rgba(255, 255, 255, 0.35);
                        color: #FFFFFF;
                    }
                    QPushButton:pressed {
                        background: rgba(255, 255, 255, 0.28);
                    }
                """)

            if hasattr(self, "btn_manage_presets") and self.btn_manage_presets:
                self.btn_manage_presets.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.12);
                        border: 1px solid rgba(255, 255, 255, 0.22);
                        border-top: 1px solid rgba(255, 255, 255, 0.50);
                        border-radius: 12px;
                        color: #FFFFFF;
                        font-size: 12.5px;
                        font-weight: 600;
                        padding: 2px 12px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.24);
                        border-color: rgba(255, 255, 255, 0.40);
                        color: #FFFFFF;
                    }
                    QPushButton:pressed {
                        background: rgba(255, 255, 255, 0.32);
                    }
                """)

            for btn in (getattr(self, "btn_work", None), getattr(self, "btn_night", None), getattr(self, "btn_sleep", None)):
                if btn:
                    btn.setStyleSheet("""
                        QPushButton {
                            background: rgba(255, 255, 255, 0.08);
                            border: 1px solid rgba(255, 255, 255, 0.16);
                            border-top: 1px solid rgba(255, 255, 255, 0.30);
                            border-radius: 12px;
                            padding: 8px 6px;
                            color: #FFFFFF;
                            font-size: 12px;
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background: rgba(255, 255, 255, 0.16);
                            border-color: rgba(255, 255, 255, 0.35);
                            color: #FFFFFF;
                        }
                        QPushButton:checked {
                            background: rgba(255, 255, 255, 0.26);
                            border: 1px solid rgba(255, 255, 255, 0.45);
                            border-top: 1.5px solid rgba(255, 255, 255, 0.85);
                            color: #FFFFFF;
                            font-weight: 700;
                        }
                    """)

            if hasattr(self, "btn_stealth") and self.btn_stealth:
                if hasattr(self.btn_stealth, "set_theme"):
                    self.btn_stealth.set_theme(self.current_theme)
        else:
            # 苹果黑天主题 (macOS Sonoma 纯正中性深色模式)
            if hasattr(self, "lbl_scale") and self.lbl_scale:
                self.lbl_scale.setVisible(False)
            if hasattr(self, "lbl_title"):
                self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 700; border: none; background: transparent; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")
            if hasattr(self, "lbl_status"):
                self.lbl_status.setStyleSheet("color: rgba(235, 235, 245, 0.75); font-size: 13.5px; font-weight: 500; border: none; background: transparent; font-family: 'Segoe UI Emoji', 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")
            if hasattr(self, "lbl_bright_title"):
                self.lbl_bright_title.setStyleSheet("color: #CBD5E1; font-size: 14px; font-weight: 500; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")
            if hasattr(self, "lbl_warmth_title"):
                self.lbl_warmth_title.setStyleSheet("color: #CBD5E1; font-size: 14px; font-weight: 500; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")
            if hasattr(self, "lbl_presets_title"):
                self.lbl_presets_title.setStyleSheet("color: #CBD5E1; font-size: 14px; font-weight: 500; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;")

            cur_b = getattr(self.engine, "current_brightness", 100)
            is_low = (cur_b <= 10) or (hasattr(self, "chip_2x") and self.chip_2x.isChecked() and cur_b <= 15)
            self._update_reset_button_affordance(is_low)

            if hasattr(self, "btn_theme_toggle") and self.btn_theme_toggle:
                self.btn_theme_toggle.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.06);
                        border: 1px solid rgba(255, 255, 255, 0.10);
                        border-radius: 12px;
                        color: rgba(235, 235, 245, 0.85);
                        font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 12.5px;
                        font-weight: 600;
                        padding: 2px 12px;
                    }
                    QPushButton:hover {
                        background: rgba(245, 179, 56, 0.18);
                        border-color: rgba(245, 179, 56, 0.48);
                        color: #F5B338;
                    }
                    QPushButton:pressed {
                        background: rgba(255, 255, 255, 0.18);
                    }
                """)

            if hasattr(self, "btn_manage_presets") and self.btn_manage_presets:
                self.btn_manage_presets.setStyleSheet("""
                    QPushButton {
                        background: rgba(245, 179, 56, 0.14);
                        color: #F5B338;
                        border: 1px solid rgba(245, 179, 56, 0.40);
                        border-radius: 12px;
                        font-family: "Segoe UI Emoji", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 12.5px;
                        font-weight: 600;
                        padding: 2px 12px;
                    }
                    QPushButton:hover {
                        background: rgba(245, 179, 56, 0.24);
                        color: #FBBF24;
                        border-color: rgba(245, 179, 56, 0.65);
                    }
                    QPushButton:pressed {
                        background: rgba(245, 179, 56, 0.35);
                    }
                """)

            for btn in (getattr(self, "btn_work", None), getattr(self, "btn_night", None), getattr(self, "btn_sleep", None)):
                if btn:
                    btn.setStyleSheet("""
                        QPushButton {
                            background: rgba(255, 255, 255, 0.05);
                            border: 1px solid rgba(255, 255, 255, 0.10);
                            border-radius: 12px;
                            padding: 8px 6px;
                            color: #CBD5E1;
                            font-size: 12px;
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background: rgba(255, 255, 255, 0.12);
                            border-color: rgba(255, 255, 255, 0.20);
                            color: #FFFFFF;
                        }
                        QPushButton:checked {
                            background: rgba(245, 179, 56, 0.18);
                            border: 1px solid #F5B338;
                            color: #F5B338;
                            font-weight: 700;
                        }
                    """)

            if hasattr(self, "btn_stealth") and self.btn_stealth:
                if hasattr(self.btn_stealth, "set_theme"):
                    self.btn_stealth.set_theme(self.current_theme)

    def cleanup_and_restore(self):
        """
        非破坏性生命周期恢复协议：
        应用退出或关闭时调用，还原系统初始硬件背光与 Gamma 色温曲线，关闭暗夜遮罩。
        """
        qapp = QApplication.instance()
        if qapp:
            try:
                qapp.removeEventFilter(self)
            except Exception:
                pass
        if hasattr(self, "hud") and self.hud:
            self.hud.close()
        if self.overlay:
            self.overlay.set_target_opacity(0.0)
            self.overlay.close()
        self.engine.restore_on_exit()

MainWindow = LunaMainWindow

__all__ = ["LunaMainWindow", "MainWindow"]
