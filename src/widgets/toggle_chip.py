"""Apple-style Pill Toggle Chip Widget (ToggleChip)

Provides an Apple macOS / iOS Control Center style pill chip with
subtle frosted acrylic glass styling, radiant amber/gold active glow,
and micro-interaction hover/pressed transitions.
"""

from typing import Optional
from PyQt5.QtCore import Qt, QSize, QRectF, pyqtSignal
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QLinearGradient,
    QFont,
    QFontMetrics,
    QPainterPath,
)
from PyQt5.QtWidgets import QPushButton, QWidget


class ToggleChip(QPushButton):
    """Pill chip button with fluid toggle states and luminous amber active accent."""

    rightClicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.RightButton:
            self.rightClicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def __init__(
        self,
        text: str = "",
        icon_symbol: str = "",
        parent: Optional[QWidget] = None,
        is_checkable: bool = True,
    ):
        super().__init__(text, parent)
        self._icon_symbol = icon_symbol
        self._accent_color = QColor(255, 180, 50)  # Radiant amber gold
        self._hovered = False
        self._theme = "dark"

        self.setCheckable(is_checkable)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy(Qt.StrongFocus))
        self.setFixedHeight(38)

        # Base typography (High readability font size)
        font = self.font()
        font.setPointSize(10)
        font.setWeight(QFont.DemiBold)
        self.setFont(font)

    def icon_symbol(self) -> str:
        return self._icon_symbol

    def setIconSymbol(self, symbol: str) -> None:
        if self._icon_symbol != symbol:
            self._icon_symbol = symbol
            self.updateGeometry()
            self.update()

    def set_accent_color(self, color: QColor) -> None:
        self._accent_color = color
        self.update()

    def set_theme(self, theme: str) -> None:
        if theme in ("dark", "light", "liquid_glass"):
            self._theme = theme
            self.update()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._hovered = True
        self.update()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._hovered = False
        self.update()

    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        text_str = self.text().strip()
        icon_str = self._icon_symbol
        if icon_str and text_str.startswith(icon_str):
            text_str = text_str[len(icon_str):].strip()

        text_width = fm.horizontalAdvance(text_str) if hasattr(fm, "horizontalAdvance") else fm.width(text_str)
        icon_width = (fm.horizontalAdvance(icon_str) + 6) if (icon_str and hasattr(fm, "horizontalAdvance")) else (fm.width(icon_str) + 6 if icon_str else 0)
        total_width = text_width + icon_width + 24  # 12px padding on each side
        return QSize(max(60, total_width), 30)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 12.0

        is_checked = self.isChecked()
        is_pressed = self.isDown()

        # Path for pill shape
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # 1. Background fill
        cur_th = getattr(self, "_theme", "dark")
        if is_checked:
            if cur_th == "light":
                # 苹果白天模式激活态：精润雪白高光卡片配 Apple 系统琥珀色边框与微阴影
                bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                bg_gradient.setColorAt(0.0, QColor(255, 255, 255, 255))
                bg_gradient.setColorAt(1.0, QColor(248, 249, 252, 255))
                painter.setBrush(QBrush(bg_gradient))
                painter.setPen(QPen(QColor(255, 149, 0, 220), 1.2))
            else:
                # Active state: luminous Apple amber gradient
                bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                accent_r = self._accent_color.red()
                accent_g = self._accent_color.green()
                accent_b = self._accent_color.blue()

                if is_pressed:
                    bg_gradient.setColorAt(0.0, QColor(accent_r, accent_g, accent_b, 85))
                    bg_gradient.setColorAt(1.0, QColor(accent_r - 20, accent_g - 20, accent_b, 65))
                elif self._hovered:
                    bg_gradient.setColorAt(0.0, QColor(accent_r, accent_g, accent_b, 75))
                    bg_gradient.setColorAt(1.0, QColor(accent_r - 20, accent_g - 20, accent_b, 55))
                else:
                    bg_gradient.setColorAt(0.0, QColor(accent_r, accent_g, accent_b, 60))
                    bg_gradient.setColorAt(1.0, QColor(accent_r - 20, accent_g - 20, accent_b, 40))

                painter.setBrush(QBrush(bg_gradient))
                painter.setPen(QPen(QColor(accent_r, accent_g, accent_b, 180), 1.0))
        else:
            # Inactive state: dark frosted vs light snow glass vs liquid glass (保持克制视觉静默)
            if cur_th == "light":
                # 苹果白天模式未激活：纯白微晶药丸卡片 (中性低透明，克制高雅)
                if is_pressed:
                    painter.setBrush(QBrush(QColor(0, 0, 0, 18)))
                    painter.setPen(QPen(QColor(0, 0, 0, 35), 0.8))
                elif self._hovered:
                    painter.setBrush(QBrush(QColor(0, 0, 0, 12)))
                    painter.setPen(QPen(QColor(0, 0, 0, 28), 0.8))
                else:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
                    painter.setPen(QPen(QColor(0, 0, 0, 20), 0.8))
            elif cur_th == "liquid_glass":
                if is_pressed:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 38)))
                    painter.setPen(QPen(QColor(255, 255, 255, 75), 0.8))
                elif self._hovered:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 26)))
                    painter.setPen(QPen(QColor(255, 255, 255, 55), 0.8))
                else:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 16)))
                    painter.setPen(QPen(QColor(255, 255, 255, 36), 0.8))
            else:
                # 苹果深色模式未激活：克制沉静的半透深灰磨砂 (消除非必要的常驻金边)
                if is_pressed:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 26)))
                    painter.setPen(QPen(QColor(255, 255, 255, 50), 0.8))
                elif self._hovered:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 18)))
                    painter.setPen(QPen(QColor(255, 255, 255, 36), 0.8))
                else:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 10)))
                    painter.setPen(QPen(QColor(255, 255, 255, 22), 0.8))

        painter.drawPath(path)

        # 2. Subtle top rim highlight
        highlight_pen = QPen(QColor(255, 255, 255, 28 if not is_checked else 50), 0.5)
        painter.setPen(highlight_pen)
        painter.setBrush(Qt.NoBrush)
        inner_rect = rect.adjusted(1.0, 1.0, -1.0, -1.0)
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner_rect, radius - 1.0, radius - 1.0)
        painter.drawPath(inner_path)

        # 3. Content: Icon + Text
        icon_str = self._icon_symbol
        text_str = self.text().strip()

        # 彻底解决双图标问题：若文字中已包含图标前缀，自动剥离重复图标
        if icon_str and text_str.startswith(icon_str):
            text_str = text_str[len(icon_str):].strip()

        icon_font = QFont("Segoe UI Emoji")
        icon_font.setPixelSize(15)
        icon_fm = QFontMetrics(icon_font)

        text_font = QFont("Microsoft YaHei UI")
        text_font.setPixelSize(13)
        text_font.setWeight(QFont.Bold)
        text_fm = QFontMetrics(text_font)

        icon_w = (icon_fm.horizontalAdvance(icon_str) if hasattr(icon_fm, "horizontalAdvance") else icon_fm.width(icon_str)) if icon_str else 0
        text_w = text_fm.horizontalAdvance(text_str) if hasattr(text_fm, "horizontalAdvance") else text_fm.width(text_str)
        gap = 7 if (icon_w > 0 and text_w > 0) else 0
        content_w = icon_w + gap + text_w

        start_x = rect.x() + (rect.width() - content_w) / 2.0
        baseline_y = rect.y() + (rect.height() + text_fm.ascent() - text_fm.descent()) / 2.0

        if is_checked:
            if getattr(self, "_theme", "dark") == "light":
                icon_color = QColor(255, 149, 0, 255)      # Apple 浅色模式琥珀金
                text_color = QColor(29, 29, 31, 255)       # Apple 炭黑字
            else:
                icon_color = QColor(255, 215, 90, 255)
                text_color = QColor(255, 240, 205, 255)
        else:
            cur_th = getattr(self, "_theme", "dark")
            if cur_th == "light":
                # 苹果白天模式深色高对比文字 (Apple #1D1D1F 墨黑)
                if self._hovered:
                    icon_color = QColor(29, 29, 31, 255)
                    text_color = QColor(29, 29, 31, 255)
                else:
                    icon_color = QColor(60, 60, 67, 230)
                    text_color = QColor(60, 60, 67, 230)
            elif cur_th == "liquid_glass":
                if self._hovered:
                    icon_color = QColor(255, 255, 255, 255)
                    text_color = QColor(255, 255, 255, 255)
                else:
                    icon_color = QColor(235, 235, 245, 200)
                    text_color = QColor(235, 235, 245, 220)
            else:
                # 苹果黑天模式：高雅银白文字
                icon_color = QColor(255, 159, 10, 230) if self._hovered else QColor(235, 235, 245, 180)
                text_color = QColor(255, 255, 255, 255) if self._hovered else QColor(235, 235, 245, 220)

        # Draw icon
        if icon_str:
            painter.setFont(icon_font)
            painter.setPen(icon_color)
            painter.drawText(int(start_x), int(baseline_y), icon_str)
            start_x += icon_w + gap

        # Draw label text
        if text_str:
            painter.setFont(text_font)
            painter.setPen(text_color)
            painter.drawText(int(start_x), int(baseline_y), text_str)

        painter.end()
