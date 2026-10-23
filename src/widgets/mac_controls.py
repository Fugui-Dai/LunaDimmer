"""Luna Dimmer - 苹果 macOS「系统设置」原生风味控件库 (Apple macOS System Settings Controls)

遵循 Apple Human Interface Guidelines (macOS Ventura / Sonoma / Sequoia):
1. MacSwitch: 像素级还原 Apple iOS/macOS 胶囊动效微动开关 (Pill Toggle Switch)；
2. MacSegmentedControl: 苹果分段胶囊选择器 (NSSegmentedControl)；
3. MacNavButton: macOS 侧边栏导航项 (26px 超椭圆彩色图标徽标 + 磨砂浮雕选中态)；
4. MacTrafficLights: 经典左上角红黄绿三色信号灯 (🔴 🟡 🟢，支持悬停矢量字符显隐)；
5. MacInsetCard & MacSettingRow: macOS 标志性 Inset Grouped 扁平卡片与发丝级微晶分割线。
"""

from typing import Optional, List, Tuple
import math

from PyQt5.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QSize,
    pyqtSignal,
    pyqtProperty,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QLinearGradient,
    QPainterPath,
    QFont,
)
from PyQt5.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QAbstractButton,
    QPushButton,
    QSizePolicy,
    QDialog,
    QGraphicsDropShadowEffect,
)


class MacSwitch(QAbstractButton):
    """
    Apple iOS/macOS 风格平滑双态微动开关 (Pill Toggle Switch):
    - 38px x 22px 标准胶囊轨道 (Track)，圆角 11px；
    - 开启时：苹果琥珀金/月光渐变 (#F5B338 -> #E89E28)，微光柔和；
    - 关闭时：半透明暗晶深灰轨道 (rgba(255, 255, 255, 0.16))；
    - 纯白悬浮立体圆形钮 (Thumb 18px)，微柔阴影；
    - 140ms OutCubic 平滑滑动过渡动效。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(38, 22)
        self.setCursor(Qt.PointingHandCursor)

        self._thumb_pos = 1.0 if self.isChecked() else 0.0
        self._anim = QPropertyAnimation(self, b"thumb_pos", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self.toggled.connect(self._on_toggled)

    def _get_thumb_pos(self) -> float:
        return self._thumb_pos

    def _set_thumb_pos(self, val: float):
        self._thumb_pos = val
        self.update()

    thumb_pos = pyqtProperty(float, _get_thumb_pos, _set_thumb_pos)

    def _on_toggled(self, checked: bool):
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._thumb_pos = 1.0 if checked else 0.0
        self.update()

    def set_theme(self, theme: str):
        if theme in ("dark", "light", "liquid_glass"):
            self._theme = theme
            self.update()

    def apply_theme(self, theme: str):
        self.set_theme(theme)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        w = float(self.width())
        h = float(self.height())
        radius = h / 2.0

        track_rect = QRectF(0.0, 0.0, w, h)
        track_path = QPainterPath()
        track_path.addRoundedRect(track_rect, radius, radius)

        # 1. 轨道底色平滑插值 (Lerp between Inactive Dark Glass and Luna Amber)
        t = self._thumb_pos
        cur_th = getattr(self, "_theme", "dark")
        grad_on = QLinearGradient(0, 0, w, h)
        if cur_th == "light":
            # 苹果白天模式：高明度琥珀橙 (对标 Image 3)
            grad_on.setColorAt(0.0, QColor(245, 158, 11, int(255 * t)))
            grad_on.setColorAt(1.0, QColor(234, 88, 12, int(255 * t)))
        elif cur_th == "liquid_glass":
            grad_on.setColorAt(0.0, QColor(251, 146, 60, int(255 * t)))
            grad_on.setColorAt(1.0, QColor(234, 88, 12, int(255 * t)))
        else:
            grad_on.setColorAt(0.0, QColor(245, 179, 56, int(255 * t)))
            grad_on.setColorAt(1.0, QColor(232, 158, 40, int(255 * t)))

        if cur_th == "light":
            off_color = QColor(0, 0, 0, int(28 * (1.0 - t)))
        else:
            off_color = QColor(255, 255, 255, int(42 * (1.0 - t)))

        p.fillPath(track_path, off_color)
        if t > 0.01:
            p.fillPath(track_path, grad_on)

        # 2. 轨道物理微边框
        border_alpha = int(35 + 45 * t)
        p.setPen(QPen(QColor(255, 255, 255, border_alpha), 0.8))
        p.drawPath(track_path)

        # 3. 悬浮纯白圆钮 (Thumb)
        thumb_dia = 18.0
        min_x = 2.0
        max_x = w - thumb_dia - 2.0
        cx = min_x + (max_x - min_x) * t
        cy = 2.0

        thumb_rect = QRectF(cx, cy, thumb_dia, thumb_dia)

        # 柔和阴影
        shadow_rect = QRectF(cx, cy + 1.2, thumb_dia, thumb_dia)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 70)))
        p.drawEllipse(shadow_rect)

        # 白色实体圆钮
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.setPen(QPen(QColor(0, 0, 0, 20), 0.5))
        p.drawEllipse(thumb_rect)


class MacSegmentedControl(QFrame):
    """
    macOS 风格分段胶囊选择器 (NSSegmentedControl):
    - 用于多语言或视图模式切换；
    - 外层暗色胶囊卡槽，激活项呈微浮雕半透明高亮。
    """
    segment_changed = pyqtSignal(str)

    def __init__(self, items: List[Tuple[str, str]], active_id: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.items = items  # [(id, label), ...]
        self.active_id = active_id
        self._buttons = {}
        self._theme = "dark"

        self.setFixedHeight(30)
        self.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.32);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 9px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        for seg_id, label in self.items:
            btn = QPushButton(label, self)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda *args, sid=seg_id: self.select_segment(sid))
            layout.addWidget(btn)
            self._buttons[seg_id] = btn

        self._refresh_styles()

    def select_segment(self, seg_id: str):
        if seg_id == self.active_id:
            return
        self.active_id = seg_id
        self._refresh_styles()
        self.segment_changed.emit(seg_id)

    def set_active_id(self, seg_id: str):
        if seg_id in self._buttons:
            self.active_id = seg_id
            self._refresh_styles()

    def update_item_labels(self, items: List[Tuple[str, str]]):
        self.items = items
        for seg_id, label in items:
            if seg_id in self._buttons:
                self._buttons[seg_id].setText(label)

    def apply_theme(self, theme: str):
        self.set_theme(theme)

    def set_theme(self, theme: str):
        if theme in ("dark", "light", "liquid_glass"):
            self._theme = theme
            if theme == "light":
                self.setStyleSheet("""
                    QFrame {
                        background: rgba(0, 0, 0, 0.06);
                        border: 1px solid rgba(0, 0, 0, 0.08);
                        border-radius: 9px;
                    }
                """)
            elif theme == "liquid_glass":
                self.setStyleSheet("""
                    QFrame {
                        background: rgba(255, 255, 255, 0.06);
                        border: 1px solid rgba(255, 255, 255, 0.16);
                        border-top: 1px solid rgba(255, 255, 255, 0.32);
                        border-radius: 9px;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QFrame {
                        background: rgba(0, 0, 0, 0.32);
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 9px;
                    }
                """)
            self._refresh_styles()

    def _refresh_styles(self):
        theme = getattr(self, "_theme", "dark")
        if theme == "light":
            # 苹果白天模式分段选择器 (对标 macOS System Settings 纯白微浮雕卡槽)
            active_style = """
                QPushButton {
                    background: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.10);
                    border-radius: 7px;
                    color: #1D1D1F;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0 9px;
                }
            """
            inactive_style = """
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 7px;
                    color: rgba(60, 60, 67, 0.65);
                    font-size: 12px;
                    font-weight: 500;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    color: #1D1D1F;
                    background: rgba(0, 0, 0, 0.04);
                }
            """
            for sid, btn in self._buttons.items():
                btn.setStyleSheet(active_style if sid == self.active_id else inactive_style)
            return
        elif theme == "liquid_glass":
            # 苹果液态玻璃模式：通透纯粹的微晶浮雕磨砂白
            active_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.22);
                    border: 1px solid rgba(255, 255, 255, 0.36);
                    border-top: 1px solid rgba(255, 255, 255, 0.70);
                    border-radius: 7px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0 9px;
                }
            """
            inactive_style = """
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 7px;
                    color: rgba(235, 235, 245, 0.65);
                    font-size: 12px;
                    font-weight: 500;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                    background: rgba(255, 255, 255, 0.10);
                }
            """
            for sid, btn in self._buttons.items():
                btn.setStyleSheet(active_style if sid == self.active_id else inactive_style)
            return

        active_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.16);
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 7px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
                padding: 0 8px;
            }
        """
        inactive_style = """
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 7px;
                color: rgba(235, 235, 245, 0.60);
                font-size: 12px;
                font-weight: 500;
                padding: 0 8px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background: rgba(255, 255, 255, 0.06);
            }
        """
        for sid, btn in self._buttons.items():
            btn.setStyleSheet(active_style if sid == self.active_id else inactive_style)


class MacNavButton(QPushButton):
    """
    macOS Ventura/Sonoma 系统设置左侧导航胶囊:
    - 26x26px 超椭圆彩色渐变图标徽标 (General=Blue, Optics=Amber, Hotkeys=Indigo, Safety=Emerald)；
    - 选中态：macOS 浮雕毛玻璃胶囊 (rgba(255, 255, 255, 0.12), radius 8px)；
    - 实体 QPushButton 架构，杜绝软抽象按钮点击失灵与拖拽边界抢占；
    - 平滑呼吸悬停反馈与 100% 矢量抗锯齿绘制。
    """

    def __init__(
        self,
        badge_icon: str,
        badge_gradient: Tuple[str, str],
        title: str,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(title, parent)
        self.badge_icon = badge_icon
        self.badge_gradient = badge_gradient
        self._title = title
        self._is_active = False
        self._hovered = False
        self._show_badge = False
        self._theme = "dark"

        self.setFixedHeight(38)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

    def sizeHint(self) -> QSize:
        return QSize(163, 38)

    def set_badge(self, show: bool):
        pass

    def set_active(self, active: bool):
        if self._is_active != active:
            self._is_active = active
            self.update()

    def set_selected(self, selected: bool):
        self.set_active(selected)

    def set_text(self, text: str):
        self.set_title(text)

    def set_title(self, title: str):
        if self._title != title:
            self._title = title
            self.update()

    def set_theme(self, theme: str):
        if theme in ("dark", "light", "liquid_glass"):
            self._theme = theme
            self.update()

    def apply_theme(self, theme: str):
        self.set_theme(theme)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mouseReleaseEvent(event)
            event.accept()
            return
        super().mouseReleaseEvent(event)

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
        p.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect())

        # 1. 胶囊背景底色 (黑天 vs 白夜 vs 液态玻璃自适应)
        current_theme = getattr(self, "_theme", "dark")
        if current_theme == "light":
            if self._is_active:
                p.setBrush(QBrush(QColor(0, 0, 0, 20)))
                p.setPen(QPen(QColor(0, 0, 0, 28), 0.8))
                p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8.0, 8.0)
            elif self._hovered:
                p.setBrush(QBrush(QColor(0, 0, 0, 10)))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8.0, 8.0)
        elif current_theme == "liquid_glass":
            if self._is_active:
                p.setBrush(QBrush(QColor(255, 255, 255, 48)))
                p.setPen(QPen(QColor(255, 255, 255, 80), 0.8))
                p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8.0, 8.0)
            elif self._hovered:
                p.setBrush(QBrush(QColor(255, 255, 255, 22)))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8.0, 8.0)
        else:
            # 苹果黑天主题侧边栏项 (对标 Image 2 选中微浮雕高亮胶囊)
            if self._is_active:
                p.setBrush(QBrush(QColor(255, 255, 255, 28)))
                p.setPen(QPen(QColor(255, 255, 255, 50), 0.8))
                p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8.0, 8.0)
            elif self._hovered:
                p.setBrush(QBrush(QColor(255, 255, 255, 16)))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8.0, 8.0)

        # 2. 绘制 26x26 超椭圆彩色徽标
        b_size = 24.0
        bx = 8.0
        by = (rect.height() - b_size) / 2.0
        badge_rect = QRectF(bx, by, b_size, b_size)
        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_rect, 6.0, 6.0)

        grad = QLinearGradient(bx, by, bx, by + b_size)
        grad.setColorAt(0.0, QColor(self.badge_gradient[0]))
        grad.setColorAt(1.0, QColor(self.badge_gradient[1]))
        p.fillPath(badge_path, grad)

        # 徽标边框
        p.setPen(QPen(QColor(255, 255, 255, 40), 0.6))
        p.drawPath(badge_path)

        # 徽标内部 Emoji / 图标字符
        font = QFont("Segoe UI Emoji", 11)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(badge_rect, Qt.AlignCenter, self.badge_icon)

        # 3. 绘制标题文字
        text_x = bx + b_size + 10.0
        text_rect = QRectF(text_x, 0, rect.width() - text_x - 8, rect.height())

        font_text = QFont("Microsoft YaHei UI", 10)
        font_text.setWeight(QFont.DemiBold if self._is_active else QFont.Normal)
        p.setFont(font_text)

        if getattr(self, "_theme", "dark") == "light":
            if self._is_active:
                p.setPen(QColor("#1D1D1F"))
            elif self._hovered:
                p.setPen(QColor("#1D1D1F"))
            else:
                p.setPen(QColor(60, 60, 67, 215))
        else:
            if self._is_active:
                p.setPen(QColor("#FFFFFF"))
            elif self._hovered:
                p.setPen(QColor("#F5F5F7"))
            else:
                p.setPen(QColor(235, 235, 245, 165))

        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self._title)


class MacTrafficLights(QWidget):
    """
    macOS 原生标准窗口控制按钮 (Traffic Lights):
    - 🔴 关闭 (Close)
    - 🟡 最小化 (Minimize)
    - 严格遵循 Apple macOS 标准规范：
      * 按钮圆点直径：12px (12x12)
      * 按钮之间间距：8px（圆心距 20px）
      * 矢量符号规范：常规纯净圆点，仅鼠标悬停整组信号灯时呈现精致微弱矢量符号 (1:1 还原 macOS 原生交互)
    """
    sig_close = pyqtSignal()
    sig_min = pyqtSignal()
    sig_minimize = sig_min

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        reverse_order: bool = False,
        show_maximize: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(parent)
        self.reverse_order = reverse_order
        self.show_maximize = show_maximize
        # 两个 12px 圆点 + 8px 间距 = 宽度 32px，高度 12px
        self.setFixedSize(32, 12)
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x()
            if self.reverse_order:
                # 倒序：左侧为最小化，右侧为关闭（分界点为中轴 16px）
                if 0 <= x <= 16:
                    self.sig_min.emit()
                elif 16 < x <= 32:
                    self.sig_close.emit()
            else:
                # 经典 Mac 顺序：左侧为关闭，右侧为最小化
                if 0 <= x <= 16:
                    self.sig_close.emit()
                elif 16 < x <= 32:
                    self.sig_min.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        if self.reverse_order:
            dots = [
                (QColor("#FFBD2E"), QColor(222, 161, 35, 230 if self._hovered else 180), QColor("#543500"), "min"),
                (QColor("#FF5F56"), QColor(224, 68, 62, 230 if self._hovered else 180), QColor("#4A0002"), "close"),
            ]
        else:
            dots = [
                (QColor("#FF5F56"), QColor(224, 68, 62, 230 if self._hovered else 180), QColor("#4A0002"), "close"),
                (QColor("#FFBD2E"), QColor(222, 161, 35, 230 if self._hovered else 180), QColor("#543500"), "min"),
            ]

        # 苹果 macOS 官方规范：直径 12px，间距 8px，两两圆心距 20px
        for i, (bg, border, symbol_color, d_type) in enumerate(dots):
            cx = 6.0 + i * 20.0
            cy = 6.0
            rect = QRectF(cx - 5.5, cy - 5.5, 11.0, 11.0)

            # 圆点背景与描边
            p.setBrush(QBrush(bg))
            p.setPen(QPen(border, 0.75))
            p.drawEllipse(rect)

            # 矢量微符号默认常驻清晰显示 (遵循用户要求：关闭与最小化图标常驻，鼠标悬停时强化笔触)
            p.setBrush(Qt.NoBrush)
            pen_w = 1.30 if self._hovered else 1.15
            sym_c = symbol_color if self._hovered else QColor(symbol_color.red(), symbol_color.green(), symbol_color.blue(), 215)
            p.setPen(QPen(sym_c, pen_w, Qt.SolidLine, Qt.RoundCap))
            if d_type == "close":
                d = 2.4
                p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
                p.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))
            elif d_type == "min":
                p.drawLine(QPointF(cx - 3.0, cy), QPointF(cx + 3.0, cy))


class MacSettingRow(QWidget):
    """
    macOS Inset Grouped 卡片行:
    - 左侧标题与副标题；
    - 右侧交互控件；
    - 底部 0.5px 发丝级分割线 (非最后一行时呈现)。
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        control: Optional[QWidget] = None,
        is_last: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.is_last = is_last
        th = getattr(parent, "_theme", getattr(parent, "theme", getattr(parent, "selected_theme", "dark")))
        self._theme = th if th in ("dark", "light", "liquid_glass") else "dark"
        self.setMinimumHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        # 左侧文本列
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self.lbl_title = QLabel(title, self)
        self.lbl_title.setStyleSheet("font-size: 13.5px; font-weight: 500; color: #FFFFFF; border: none; background: transparent;")
        text_col.addWidget(self.lbl_title)

        if subtitle:
            self.lbl_sub = QLabel(subtitle, self)
            self.lbl_sub.setStyleSheet("font-size: 12px; line-height: 17px; color: rgba(235, 235, 245, 0.65); border: none; background: transparent;")
            self.lbl_sub.setWordWrap(True)
            text_col.addWidget(self.lbl_sub)
        else:
            self.lbl_sub = None

        layout.addLayout(text_col, 1)

        # 右侧控件
        if control:
            self.control = control
            layout.addWidget(control, 0, Qt.AlignVCenter)
        else:
            self.control = None

        self.set_theme(self._theme)

    def apply_theme(self, theme: str):
        self.set_theme(theme)

    def set_theme(self, theme: str):
        if theme in ("dark", "light", "liquid_glass"):
            self._theme = theme
            if theme == "light":
                self.lbl_title.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #1D1D1F; border: none; background: transparent;")
                if self.lbl_sub:
                    self.lbl_sub.setStyleSheet("font-size: 12px; line-height: 17px; color: rgba(60, 60, 67, 0.70); border: none; background: transparent;")
            elif theme == "liquid_glass":
                self.lbl_title.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #FFFFFF; border: none; background: transparent;")
                if self.lbl_sub:
                    self.lbl_sub.setStyleSheet("font-size: 12px; line-height: 17px; color: rgba(235, 235, 245, 0.70); border: none; background: transparent;")
            else:
                self.lbl_title.setStyleSheet("font-size: 13.5px; font-weight: 500; color: #FFFFFF; border: none; background: transparent;")
                if self.lbl_sub:
                    self.lbl_sub.setStyleSheet("font-size: 12px; line-height: 17px; color: rgba(235, 235, 245, 0.65); border: none; background: transparent;")
            if hasattr(self, "control") and self.control and hasattr(self.control, "set_theme"):
                self.control.set_theme(theme)
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.is_last:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing, False)
            line_color = QColor(0, 0, 0, 16) if getattr(self, "_theme", "dark") == "light" else QColor(255, 255, 255, 16)
            pen = QPen(line_color, 1.0)
            p.setPen(pen)
            y = self.height() - 1
            p.drawLine(14, y, self.width() - 14, y)


class MacInsetCard(QFrame):
    """
    macOS Inset Grouped 扁平圆角卡片容器:
    - 采用 QPainter 硬件抗锯齿绘制 13px 超椭圆圆角，从根本上消灭 Windows Qt 下 border-radius 偶发回退为直角矩形的 Bug；
    - 半透明冷暗晶质底 / 白夜浅灰高质感底；
    - 包含多行设置并自动组织内嵌布局。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        th = getattr(parent, "_theme", getattr(parent, "theme", getattr(parent, "selected_theme", "dark")))
        self._theme = th if th in ("dark", "light", "liquid_glass") else "dark"
        self._rows = []
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(0)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.6, 0.6, -0.6, -0.6)
        path = QPainterPath()
        path.addRoundedRect(rect, 13.0, 13.0)

        th = getattr(self, "_theme", "dark")
        if th == "light":
            p.fillPath(path, QBrush(QColor(255, 255, 255, 248)))
            p.setPen(QPen(QColor(0, 0, 0, 24), 0.9))
        elif th == "liquid_glass":
            p.fillPath(path, QBrush(QColor(255, 255, 255, 20)))
            p.setPen(QPen(QColor(255, 255, 255, 52), 0.9))
        else:
            p.fillPath(path, QBrush(QColor(255, 255, 255, 11)))
            p.setPen(QPen(QColor(255, 255, 255, 22), 0.9))
        p.drawPath(path)

    def set_theme(self, theme: str):
        if theme in ("dark", "light", "liquid_glass"):
            self._theme = theme
            self.update()
            for i in range(self.card_layout.count()):
                item = self.card_layout.itemAt(i)
                if item and item.widget() and hasattr(item.widget(), "set_theme"):
                    item.widget().set_theme(theme)
            for row in getattr(self, "_rows", []):
                if hasattr(row, "set_theme"):
                    row.set_theme(theme)

    def apply_theme(self, theme: str):
        self.set_theme(theme)

    def add_row(self, row: MacSettingRow):
        if not hasattr(self, "_rows"):
            self._rows = []
        self._rows.append(row)
        if hasattr(self, "_theme") and hasattr(row, "set_theme"):
            row.set_theme(self._theme)
        self.card_layout.addWidget(row)

    def apply_theme(self, theme: str):
        self.set_theme(theme)


class AppleScaleGuide(QWidget):
    """
    苹果风格微晶临界刻度指示栏 (对标设计图 Image 1):
    - 呈现: 1% 极限微光 ··· 10% 硬件最低背光 ──────── 100% 满额
    - 采用两翼弹性自适应伸缩布局，高分屏下绝不截断；
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme = "dark"
        self.setFixedHeight(18)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        # 1. 左侧：1% 极限微光 ···
        self.lbl_left = QLabel("1% 极限微光 ···", self)
        self.lbl_left.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.lbl_left)

        layout.addStretch(1)

        # 2. 中间：10% 硬件最低背光 ────────
        self.badge_mid = QLabel("10% 硬件最低背光 ────────", self)
        self.badge_mid.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.badge_mid)

        layout.addStretch(1)

        # 3. 右侧：100% 满额
        self.lbl_right = QLabel("100% 满额", self)
        self.lbl_right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.lbl_right)

        self.apply_theme("dark")

    def retranslate(self):
        from src.i18n import t, get_language
        lang = get_language()
        if lang == "en-US":
            self.lbl_left.setText("1% Sub-Zero ···")
            self.badge_mid.setText("10% Hardware Floor ────────")
            self.lbl_right.setText("100% Full")
        else:
            self.lbl_left.setText("1% 极限微光 ···")
            self.badge_mid.setText("10% 硬件最低背光 ────────")
            self.lbl_right.setText("100% 满额")

    def setText(self, *args, **kwargs):
        self.retranslate()

    def set_theme(self, theme: str):
        self.apply_theme(theme)

    def apply_theme(self, theme: str):
        self._theme = theme
        if theme == "liquid_glass":
            style = "font-size: 12px; font-weight: 500; color: rgba(235, 235, 245, 0.65); border: none; background: transparent; letter-spacing: 0.2px;"
            self.lbl_left.setStyleSheet(style)
            self.lbl_right.setStyleSheet(style)
            self.badge_mid.setStyleSheet(style)
        elif theme == "light":
            style = "font-size: 12px; font-weight: 500; color: rgba(60, 60, 67, 0.65); border: none; background: transparent;"
            self.lbl_left.setStyleSheet(style)
            self.lbl_right.setStyleSheet(style)
            self.badge_mid.setStyleSheet(style)
        else:
            style = "font-size: 12px; font-weight: 500; color: rgba(235, 235, 245, 0.60); border: none; background: transparent;"
            self.lbl_left.setStyleSheet(style)
            self.lbl_right.setStyleSheet(style)
            self.badge_mid.setStyleSheet(style)


class MacConfirmDialog(QDialog):
    """
    Apple macOS 原生风格危险操作确认模态对话框 (Modal Danger Confirmation Sheet)
    - 专门针对如「恢复软件出厂默认设置」等不可逆高危操作；
    - 醒目警示徽标 (⚠️ 柔光红金圆角徽章)；
    - 危险后果明细列表 (卡片内凹列出将受影响的具体设置)；
    - 双操作按钮：取消 (Esc/默认焦点安全项) 与 确定重置 (红色危险警示高亮按钮)；
    - 支持 深色 (dark)、浅色 (light)、液态玻璃 (liquid_glass) 完美适配；
    - 柔和毛玻璃阴影与 Apple 14px 超椭圆圆角。
    """

    def __init__(
        self,
        title: str = "恢复软件出厂默认设置？",
        desc: str = "此操作属于危险操作，执行后将清除所有个性化偏好且无法撤销：",
        details: Optional[List[str]] = None,
        confirm_text: str = "确定恢复出厂设置",
        cancel_text: str = "取消",
        is_destructive: bool = True,
        theme: str = "dark",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self._theme = theme
        self.setFixedWidth(452)  # 卡片净宽 420px + 双侧各 16px 弥散阴影边距

        self._detail_dots = []
        self._detail_texts = []

        # 根布局（留出投影边距）
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(0)

        # 主卡片容器 (macOS Alert Sheet Inset Card, 宽度精确对齐网页端 420px)
        self.card = QFrame(self)
        self.card.setObjectName("macConfirmCard")
        self.card.setFixedWidth(420)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 22, 24, 20)
        card_layout.setSpacing(12)

        # 苹果风柔和弥散阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 160 if theme != "light" else 60))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        # 1. 顶部 Header：警示图标徽章 (38x38 危险红光圆角徽章) + 危险操作标题 (15px Bold)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(12)

        self.icon_badge = QLabel("⚠️", self.card)
        self.icon_badge.setFixedSize(38, 38)
        self.icon_badge.setAlignment(Qt.AlignCenter)

        self.lbl_title = QLabel(title, self.card)
        self.lbl_title.setWordWrap(True)

        header_row.addWidget(self.icon_badge)
        header_row.addWidget(self.lbl_title, 1)
        card_layout.addLayout(header_row)

        # 2. 警示副标题 / 说明 (12px 次级文字，对齐网页端)
        self.lbl_desc = QLabel(desc, self.card)
        self.lbl_desc.setWordWrap(True)
        card_layout.addWidget(self.lbl_desc)

        # 3. 危险后果明细卡片（内凹列表，展示恢复受影响项目）
        if details:
            self.details_box = QFrame(self.card)
            self.details_box.setObjectName("macConfirmDetails")
            det_layout = QVBoxLayout(self.details_box)
            det_layout.setContentsMargins(14, 12, 14, 12)
            det_layout.setSpacing(6)

            for raw_item in details:
                item_text = raw_item.lstrip("• ").strip()
                row_item = QHBoxLayout()
                row_item.setContentsMargins(0, 0, 0, 0)
                row_item.setSpacing(8)
                dot = QLabel("•", self.details_box)
                dot.setFixedWidth(12)
                dot.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
                text_lbl = QLabel(item_text, self.details_box)
                text_lbl.setWordWrap(True)
                row_item.addWidget(dot)
                row_item.addWidget(text_lbl, 1)
                det_layout.addLayout(row_item)
                self._detail_dots.append(dot)
                self._detail_texts.append(text_lbl)

            card_layout.addWidget(self.details_box)

        # 4. 底部操作按钮行：取消 (默认安全键) 与 确定重置 (macOS 危险操作渐变红键)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 6, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch(1)

        self.btn_cancel = QPushButton(cancel_text, self.card)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(32)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton(confirm_text, self.card)
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.setFixedHeight(32)
        self.btn_confirm.setDefault(True)
        self.btn_confirm.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_confirm)

        card_layout.addLayout(btn_layout)
        root_layout.addWidget(self.card)

        self.apply_theme(theme, is_destructive)

    def paintEvent(self, event):
        """确保无边框透明窗口背景完全清洁，消除 Windows DWM 黑色边缘瑕疵"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    def showEvent(self, event):
        """展示时自适应父窗口绝对居中对齐"""
        super().showEvent(event)
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2,
            )

    def apply_theme(self, theme: str, is_destructive: bool = True):
        self._theme = theme
        if theme == "light":
            self.card.setStyleSheet("""
                QFrame#macConfirmCard {
                    background: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 14px;
                }
            """)
            self.icon_badge.setStyleSheet("""
                QLabel {
                    background: rgba(255, 59, 48, 0.12);
                    border: 1px solid rgba(255, 59, 48, 0.28);
                    border-radius: 10px;
                    font-size: 18px;
                }
            """)
            self.lbl_title.setStyleSheet("""
                QLabel {
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 15px;
                    font-weight: 700;
                    color: #1D1D1F;
                    line-height: 22px;
                }
            """)
            self.lbl_desc.setStyleSheet("""
                QLabel {
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                    color: #475569;
                    line-height: 18px;
                }
            """)
            if hasattr(self, "details_box"):
                self.details_box.setStyleSheet("""
                    QFrame#macConfirmDetails {
                        background: rgba(0, 0, 0, 0.035);
                        border: 1px solid rgba(0, 0, 0, 0.08);
                        border-radius: 8px;
                    }
                    QLabel {
                        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 11.5px;
                        color: #1E293B;
                        line-height: 18px;
                    }
                """)
                for dot in self._detail_dots:
                    dot.setStyleSheet("color: #DC2626; font-size: 14px; font-weight: bold;")
            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 8px;
                    color: #334155;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.09);
                    border-color: rgba(0, 0, 0, 0.20);
                    color: #0F172A;
                }
                QPushButton:pressed {
                    background: rgba(0, 0, 0, 0.14);
                }
            """)
        elif theme == "liquid_glass":
            self.card.setStyleSheet("""
                QFrame#macConfirmCard {
                    background: rgba(20, 22, 30, 0.94);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-top: 1.2px solid rgba(255, 255, 255, 0.38);
                    border-radius: 14px;
                }
            """)
            self.icon_badge.setStyleSheet("""
                QLabel {
                    background: rgba(239, 68, 68, 0.20);
                    border: 1px solid rgba(239, 68, 68, 0.40);
                    border-radius: 10px;
                    font-size: 18px;
                }
            """)
            self.lbl_title.setStyleSheet("""
                QLabel {
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 15px;
                    font-weight: 700;
                    color: #FFFFFF;
                    line-height: 22px;
                }
            """)
            self.lbl_desc.setStyleSheet("""
                QLabel {
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                    color: rgba(226, 232, 240, 0.85);
                    line-height: 18px;
                }
            """)
            if hasattr(self, "details_box"):
                self.details_box.setStyleSheet("""
                    QFrame#macConfirmDetails {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.10);
                        border-radius: 8px;
                    }
                    QLabel {
                        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 11.5px;
                        color: #F1F5F9;
                        line-height: 18px;
                    }
                """)
                for dot in self._detail_dots:
                    dot.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")
            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.16);
                    border-radius: 8px;
                    color: #E2E8F0;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.16);
                    border-color: rgba(255, 255, 255, 0.28);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.22);
                }
            """)
        else:  # Dark - 完全对齐设置中心与预设窗口的标准中性黑曜石 #1C1C1E
            self.card.setStyleSheet("""
                QFrame#macConfirmCard {
                    background: #1C1C1E;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 14px;
                }
            """)
            self.icon_badge.setStyleSheet("""
                QLabel {
                    background: rgba(239, 68, 68, 0.16);
                    border: 1px solid rgba(239, 68, 68, 0.35);
                    border-radius: 10px;
                    font-size: 18px;
                }
            """)
            self.lbl_title.setStyleSheet("""
                QLabel {
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 15px;
                    font-weight: 700;
                    color: #FFFFFF;
                    line-height: 22px;
                }
            """)
            self.lbl_desc.setStyleSheet("""
                QLabel {
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                    color: rgba(235, 235, 245, 0.65);
                    line-height: 18px;
                }
            """)
            if hasattr(self, "details_box"):
                self.details_box.setStyleSheet("""
                    QFrame#macConfirmDetails {
                        background: rgba(255, 255, 255, 0.04);
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 8px;
                    }
                    QLabel {
                        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                        font-size: 11.5px;
                        color: #E2E8F0;
                        line-height: 18px;
                    }
                """)
                for dot in self._detail_dots:
                    dot.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")
            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 8px;
                    color: #CBD5E1;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.14);
                    border-color: rgba(255, 255, 255, 0.25);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.20);
                }
            """)

        # 危险操作按钮高亮样式（macOS Ventura 风格红底渐变白字）
        if is_destructive:
            self.btn_confirm.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EF4444, stop:1 #DC2626);
                    border: 1px solid #B91C1C;
                    border-radius: 8px;
                    color: #FFFFFF;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0 18px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F87171, stop:1 #EF4444);
                    border-color: #DC2626;
                }
                QPushButton:pressed {
                    background: #B91C1C;
                    border-color: #991B1B;
                }
            """)
        else:
            self.btn_confirm.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007AFF, stop:1 #0062CC);
                    border: 1px solid #0051AB;
                    border-radius: 8px;
                    color: #FFFFFF;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0 18px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A8CFF, stop:1 #007AFF);
                    border-color: #0062CC;
                }
                QPushButton:pressed {
                    background: #0051AB;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, "_drag_pos"):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
