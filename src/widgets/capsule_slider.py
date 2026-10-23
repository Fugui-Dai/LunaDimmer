"""Apple Control Center Squircle Capsule Slider (CapsuleSlider)

Provides a thick rounded capsule track with dynamic icon, animated fill,
smooth hover wheel & keyboard navigation, and zero-jitter tabular figures.
"""

from typing import Optional
from PyQt5.QtCore import Qt, QSize, QRectF, pyqtSignal, QPointF
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QLinearGradient,
    QRadialGradient,
    QFont,
    QPainterPath,
    QMouseEvent,
    QWheelEvent,
    QKeyEvent,
)
from PyQt5.QtWidgets import QWidget


class CapsuleSlider(QWidget):
    """Apple Control Center thick squircle capsule slider."""

    valueChanged = pyqtSignal(int)
    sliderReleased = pyqtSignal()

    def __init__(
        self,
        title: str = "",
        icon_symbol: str = "☀️",
        min_val: int = 1,
        max_val: int = 100,
        parent: Optional[QWidget] = None,
        accent_mode: str = "brightness",
    ):
        super().__init__(parent)
        self._title = title
        self._icon_symbol = icon_symbol
        self._min = min_val
        self._max = max_val
        self._value = max(min_val, min(max_val, 50))
        self._accent_mode = accent_mode
        self._theme = "dark"
        self._unit = "%"
        self._show_percentage = True

        self._is_dragging = False
        self._hovered = False

        self.setFixedHeight(44)
        self.setFocusPolicy(Qt.FocusPolicy(Qt.StrongFocus))
        self.setCursor(Qt.PointingHandCursor)

    # -------------------------------------------------------------------------
    # Properties & Getters/Setters
    # -------------------------------------------------------------------------
    def value(self) -> int:
        return self._value

    def setValue(self, val: int) -> None:
        clamped = max(self._min, min(self._max, int(round(val))))
        if clamped != self._value:
            self._value = clamped
            self.update()
            self.valueChanged.emit(self._value)

    def minimum(self) -> int:
        return self._min

    def maximum(self) -> int:
        return self._max

    def setRange(self, min_val: int, max_val: int) -> None:
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        self._min = min_val
        self._max = max_val
        self.setValue(self._value)

    def title(self) -> str:
        return self._title

    def setTitle(self, title: str) -> None:
        self._title = title
        self.update()

    def icon(self) -> str:
        return self._icon_symbol

    def setIcon(self, icon: str) -> None:
        self._icon_symbol = icon
        self.update()

    def unit(self) -> str:
        return self._unit

    def setUnit(self, unit: str) -> None:
        self._unit = unit

    def set_theme(self, theme: str) -> None:
        if theme in ("dark", "light", "liquid_glass") and theme != self._theme:
            self._theme = theme
            self.update()
        self.update()

    def accent_mode(self) -> str:
        return self._accent_mode

    def set_accent_mode(self, mode: str) -> None:
        self._accent_mode = mode
        self.update()

    @property
    def is_dragging(self) -> bool:
        return self._is_dragging

    def sizeHint(self) -> QSize:
        return QSize(260, 42)

    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------
    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._hovered = True
        self.update()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._hovered = False
        self.update()

    def _val_from_x(self, x: float) -> int:
        w = max(1.0, float(self.width()))
        ratio = max(0.0, min(1.0, x / w))
        return int(round(self._min + ratio * (self._max - self._min)))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            pos_x = event.pos().x() if hasattr(event, "pos") else event.x()
            self.setValue(self._val_from_x(pos_x))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_dragging:
            pos_x = event.pos().x() if hasattr(event, "pos") else event.x()
            self.setValue(self._val_from_x(pos_x))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.sliderReleased.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            delta = event.pixelDelta().y()
        step = 2 if abs(delta) >= 120 else 1
        if delta > 0:
            self.setValue(self._value + step)
        elif delta < 0:
            self.setValue(self._value - step)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()
        step = 5 if (modifiers & Qt.ShiftModifier) else 1
        if key in (Qt.Key_Right, Qt.Key_Up):
            self.setValue(self._value + step)
            event.accept()
        elif key in (Qt.Key_Left, Qt.Key_Down):
            self.setValue(self._value - step)
            event.accept()
        elif key == Qt.Key_PageUp:
            self.setValue(self._value + 10)
            event.accept()
        elif key == Qt.Key_PageDown:
            self.setValue(self._value - 10)
            event.accept()
        else:
            super().keyPressEvent(event)

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2.0

        # Outer capsule container path
        capsule_path = QPainterPath()
        capsule_path.addRoundedRect(rect, radius, radius)

        # 1. Base track background (dark/light/liquid_glass adaptive)
        cur_th = getattr(self, "_theme", "dark")
        if cur_th == "light":
            # 苹果白天模式：轻雅内陷哑光轨道
            bg_alpha = 20 if (self._hovered or self._is_dragging) else 14
            painter.setBrush(QBrush(QColor(0, 0, 0, bg_alpha)))
            painter.setPen(QPen(QColor(0, 0, 0, 24 if self._hovered else 16), 0.8))
        elif cur_th == "liquid_glass":
            bg_alpha = 34 if (self._hovered or self._is_dragging) else 24
            painter.setBrush(QBrush(QColor(255, 255, 255, bg_alpha)))
            painter.setPen(QPen(QColor(255, 255, 255, 65 if self._hovered else 40), 0.8))
        else:
            # 苹果黑天主题：深色下陷暗槽底衬 (对标 Image 1)
            painter.setBrush(QBrush(QColor(0, 0, 0, 95 if (self._hovered or self._is_dragging) else 80)))
            if self._accent_mode == "warmth":
                track_pen_color = QColor(255, 149, 0, 32 if self._hovered else 20)
            else:
                track_pen_color = QColor(255, 255, 255, 28 if self._hovered else 18)
            painter.setPen(QPen(track_pen_color, 0.8))
        painter.drawPath(capsule_path)

        # 2. Fill progress
        span = max(1, self._max - self._min)
        ratio = max(0.0, min(1.0, (self._value - self._min) / float(span)))
        fill_width = rect.width() * ratio

        if fill_width > 0.5:
            painter.save()
            painter.setClipPath(capsule_path)

            fill_rect = QRectF(rect.x(), rect.y(), fill_width, rect.height())
            cur_th = getattr(self, "_theme", "dark")
            fill_gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())

            if self._accent_mode == "warmth":
                # Apple Night Shift 纯正日光琥珀温润流体柱 (绝无杂色发白，饱和温润)
                if cur_th == "light":
                    fill_gradient.setColorAt(0.0, QColor(255, 165, 30, 245))
                    fill_gradient.setColorAt(0.5, QColor(255, 140, 0, 250))
                    fill_gradient.setColorAt(1.0, QColor(230, 100, 0, 255))
                elif cur_th == "liquid_glass":
                    fill_gradient.setColorAt(0.0, QColor(255, 170, 40, 220))
                    fill_gradient.setColorAt(0.5, QColor(255, 145, 10, 235))
                    fill_gradient.setColorAt(1.0, QColor(235, 110, 10, 245))
                else:
                    fill_gradient.setColorAt(0.0, QColor(255, 165, 30, 255))
                    fill_gradient.setColorAt(0.5, QColor(255, 140, 0, 255))
                    fill_gradient.setColorAt(1.0, QColor(230, 95, 0, 255))
            else:
                # Apple Control Center 高通透微晶白流体 (对标网页端渐变水银柱)
                if cur_th == "light":
                    fill_gradient.setColorAt(0.0, QColor(255, 255, 255, 255))
                    fill_gradient.setColorAt(1.0, QColor(248, 249, 252, 255))
                elif cur_th == "liquid_glass":
                    fill_gradient.setColorAt(0.0, QColor(255, 255, 255, 245))
                    fill_gradient.setColorAt(1.0, QColor(242, 246, 255, 235))
                else:
                    fill_gradient.setColorAt(0.0, QColor(226, 232, 240, 245))
                    fill_gradient.setColorAt(0.6, QColor(248, 250, 252, 255))
                    fill_gradient.setColorAt(1.0, QColor(255, 255, 255, 255))

            painter.setBrush(QBrush(fill_gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRect(fill_rect)

            # 填充前缘微光切线 (仅在白银亮度滑块上绘制 1.2px 水银白光，色温滑块保持绝对纯净金橙无杂白)
            if fill_width > 3.0 and self._accent_mode != "warmth":
                spec_color = QColor(255, 255, 255, 230)
                spec_pen = QPen(spec_color, 1.2)
                painter.setPen(spec_pen)
                painter.drawLine(int(fill_rect.right()), int(rect.top() + 2), int(fill_rect.right()), int(rect.bottom() - 2))

            painter.restore()

        # 3. Inner squircle rim reflection (色温滑块采用专属琥珀微光，杜绝白光干扰)
        painter.save()
        painter.setBrush(Qt.NoBrush)
        rim_color = QColor(255, 149, 0, 18) if self._accent_mode == "warmth" else QColor(255, 255, 255, 15)
        painter.setPen(QPen(rim_color, 0.5))
        inner_path = QPainterPath()
        inner_path.addRoundedRect(rect.adjusted(1.0, 1.0, -1.0, -1.0), radius - 1.0, radius - 1.0)
        painter.drawPath(inner_path)
        painter.restore()

        # 4. Icon & Tabular Numbers with dual-contrast mask
        # Inside fill -> dark charcoal; outside fill -> luminous silver
        self._draw_overlay_content(painter, rect, fill_width)

        painter.end()

    def _draw_overlay_content(self, painter: QPainter, rect: QRectF, fill_width: float) -> None:
        """Renders icon and tabular number with Apple-style adaptive color inversion."""
        icon_rect = QRectF(rect.x() + 16.0, rect.y(), 26.0, rect.height())
        num_rect = QRectF(rect.right() - 72.0, rect.y(), 56.0, rect.height())

        icon_font = QFont("Segoe UI Emoji")
        if self._icon_symbol == "🕯️":
            icon_font.setPixelSize(17)  # 🕯️ 蜡烛字符视觉面积等权放大，与 ☀️ 达成饱满视觉平衡
        else:
            icon_font.setPixelSize(16)

        num_font = QFont("Segoe UI")
        num_font.setPixelSize(15)
        num_font.setWeight(QFont.Bold)
        # Tabular figures formatting
        num_font.setStyleHint(QFont.Monospace)

        value_str = f"{self._value}{self._unit}"

        # 1. 绘制暗部/未填充底槽图层 (未被滑块覆盖区域)
        painter.save()
        painter.setClipRect(QRectF(rect.x() + fill_width, rect.y(), rect.width() - fill_width, rect.height()))

        painter.setFont(icon_font)
        cur_th = getattr(self, "_theme", "dark")
        if cur_th == "light":
            unfilled_color = QColor(29, 29, 31, 230)  # Apple #1D1D1F 极简炭黑
        elif cur_th == "liquid_glass":
            unfilled_color = QColor(245, 245, 250, 240)
        else:
            unfilled_color = QColor(240, 242, 248, 225)
        painter.setPen(unfilled_color)
        painter.drawText(icon_rect, Qt.AlignCenter, self._icon_symbol)

        if self._show_percentage:
            painter.setFont(num_font)
            painter.setPen(unfilled_color)
            painter.drawText(num_rect, Qt.AlignRight | Qt.AlignVCenter, value_str)
        painter.restore()

        # 2. 绘制亮部/已填充前景色图层 (滑块内部精准反色)
        if fill_width > 0.5:
            painter.save()
            painter.setClipRect(QRectF(rect.x(), rect.y(), fill_width, rect.height()))

            if self._accent_mode == "warmth":
                filled_text_color = QColor(43, 18, 2, 245)   # 琥珀色柱内沉稳深棕字
            else:
                filled_text_color = QColor(29, 29, 31, 240)  # 纯白柱内 Apple 纯正炭黑字

            painter.setFont(icon_font)
            painter.setPen(filled_text_color)
            painter.drawText(icon_rect, Qt.AlignCenter, self._icon_symbol)

            if self._show_percentage:
                painter.setFont(num_font)
                painter.setPen(filled_text_color)
                painter.drawText(num_rect, Qt.AlignRight | Qt.AlignVCenter, value_str)
            painter.restore()
