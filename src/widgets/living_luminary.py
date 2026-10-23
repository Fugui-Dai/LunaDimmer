"""Living Luminary Celestial Orb Widget (LivingLuminary)

Dynamic celestial core representing the screen's light environment:
- Day (>70%): Radiant golden solar corona with ambient aura
- Night (20%~70%): Silver-white crescent moon with soft pearlescent glow
- Deep Sleep (<20%): Soothing breathing starlight pulse (12-second rhythm)
"""

import math
from typing import Optional
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF, QTimer
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QRadialGradient,
    QLinearGradient,
    QPainterPath,
)
from PyQt5.QtWidgets import QWidget


class LivingLuminary(QWidget):
    """Dynamic celestial ambient orb with Apple-inspired fluid states."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._brightness = 50
        self._warmth = 0
        self._is_sleep = False
        self._mode = "night"  # "day" | "night" | "sleep"

        # 12-second breathing pulse cycle (12000 ms)
        self._breathing_period_ms = 12000.0
        self._elapsed_ms = 0.0
        self._pulse_phase = 0.0

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(40)  # ~25 FPS for smooth low-CPU breathing
        self._pulse_timer.timeout.connect(self._on_pulse_tick)

        self.setFixedSize(38, 38)
        self.setAttribute(Qt.WA_Hover, True)
        self._update_mode()

    # -------------------------------------------------------------------------
    # State & Mode Management
    # -------------------------------------------------------------------------
    def set_state(self, brightness: int, warmth: int, is_sleep: bool = False) -> None:
        self._brightness = max(0, min(100, int(brightness)))
        self._warmth = max(0, min(100, int(warmth)))
        self._is_sleep = bool(is_sleep)
        self._update_mode()
        self.update()

    def _update_mode(self) -> None:
        old_mode = self._mode
        if self._is_sleep or self._brightness < 20:
            self._mode = "sleep"
        elif self._brightness > 70:
            self._mode = "day"
        else:
            self._mode = "night"

        if self._mode == "sleep":
            if not self._pulse_timer.isActive():
                self._pulse_timer.start()
        else:
            if self._pulse_timer.isActive():
                self._pulse_timer.stop()
            self._pulse_phase = 0.0

        if old_mode != self._mode:
            self.update()

    def _on_pulse_tick(self) -> None:
        self._elapsed_ms += self._pulse_timer.interval()
        if self._elapsed_ms >= self._breathing_period_ms:
            self._elapsed_ms = self._elapsed_ms % self._breathing_period_ms

        # Smooth sine breathing curve (0.0 to 1.0)
        angle = (2.0 * math.pi * self._elapsed_ms) / self._breathing_period_ms
        self._pulse_phase = (math.sin(angle - math.pi / 2.0) + 1.0) / 2.0
        self.update()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def brightness(self) -> int:
        return self._brightness

    @property
    def warmth(self) -> int:
        return self._warmth

    @property
    def is_sleep(self) -> bool:
        return self._is_sleep

    @property
    def is_breathing(self) -> bool:
        return self._pulse_timer.isActive()

    def sizeHint(self) -> QSize:
        return QSize(52, 52)

    def hideEvent(self, event) -> None:
        if self._pulse_timer.isActive():
            self._pulse_timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._mode == "sleep" and not self._pulse_timer.isActive():
            self._pulse_timer.start()

    # -------------------------------------------------------------------------
    # QPainter Rendering
    # -------------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        rect = QRectF(self.rect())
        cx = rect.center().x()
        cy = rect.center().y()
        base_r = min(rect.width(), rect.height()) * 0.44

        if self._mode == "day":
            self._paint_day_sun(painter, cx, cy, base_r)
        elif self._mode == "night":
            self._paint_night_moon(painter, cx, cy, base_r)
        else:
            self._paint_sleep_starlight(painter, cx, cy, base_r)

        painter.end()

    def _paint_day_sun(self, painter: QPainter, cx: float, cy: float, r: float) -> None:
        """Render golden solar core matching Web orbPreview (#ffe285 20%, #f5a623 80%)."""
        warm_ratio = self._warmth / 100.0

        # Clean spherical solar gradient fitting within 38x38 without clipped borders
        aura_grad = QRadialGradient(cx, cy, r)
        aura_grad.setColorAt(0.0, QColor(255, 240, 150, 255))
        aura_grad.setColorAt(0.30, QColor(255, int(195 + warm_ratio * 15), 45, 240))
        aura_grad.setColorAt(0.80, QColor(245, 166, 35, 230))
        aura_grad.setColorAt(1.0, QColor(230, 130, 20, 200))
        painter.setBrush(QBrush(aura_grad))
        painter.setPen(QPen(QColor(255, 245, 180, 150), 1.0))
        painter.drawEllipse(QPointF(cx, cy), r - 1.0, r - 1.0)

    def _paint_night_moon(self, painter: QPainter, cx: float, cy: float, r: float) -> None:
        """Render silver-white crescent moon with subtle pearlescent aura."""
        warm_ratio = self._warmth / 100.0

        # 1. Soft moonlight glow
        glow_r = r * 1.4
        glow_grad = QRadialGradient(cx, cy, glow_r)
        glow_r_val = int(210 + warm_ratio * 35)
        glow_g_val = int(225 + warm_ratio * 15)
        glow_b_val = int(245 - warm_ratio * 40)
        glow_grad.setColorAt(0.0, QColor(glow_r_val, glow_g_val, glow_b_val, 45))
        glow_grad.setColorAt(1.0, QColor(glow_r_val, glow_g_val, glow_b_val, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # 2. Construct Crescent Moon path
        full_moon = QPainterPath()
        full_moon.addEllipse(QPointF(cx, cy), r, r)

        mask_moon = QPainterPath()
        mask_r = r * 0.86
        mask_moon.addEllipse(QPointF(cx + r * 0.52, cy - r * 0.12), mask_r, mask_r)

        crescent = full_moon.subtracted(mask_moon)

        # 3. Moonlight gradient fill
        moon_grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        moon_grad.setColorAt(0.0, QColor(255, int(250 + warm_ratio * 5), int(255 - warm_ratio * 20)))
        moon_grad.setColorAt(0.7, QColor(int(215 + warm_ratio * 30), int(225 + warm_ratio * 10), int(240 - warm_ratio * 40)))
        moon_grad.setColorAt(1.0, QColor(int(175 + warm_ratio * 40), int(190 + warm_ratio * 20), int(210 - warm_ratio * 40)))

        painter.setBrush(QBrush(moon_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 0.6))
        painter.drawPath(crescent)

    def _paint_sleep_starlight(self, painter: QPainter, cx: float, cy: float, r: float) -> None:
        """Render breathing starlight pulse with 12s calming rhythm."""
        pulse = self._pulse_phase
        warm_ratio = self._warmth / 100.0

        # Pulse dynamic parameters
        scale = 0.88 + 0.22 * pulse
        glow_alpha = int(25 + 40 * pulse)

        # 1. Pulsing ambient aura
        aura_r = r * 1.55 * scale
        aura_grad = QRadialGradient(cx, cy, aura_r)
        a_r = int(190 + warm_ratio * 55)
        a_g = int(200 + warm_ratio * 25)
        a_b = int(245 - warm_ratio * 60)
        aura_grad.setColorAt(0.0, QColor(a_r, a_g, a_b, glow_alpha))
        aura_grad.setColorAt(0.65, QColor(a_r, a_g, a_b, int(glow_alpha * 0.35)))
        aura_grad.setColorAt(1.0, QColor(a_r, a_g, a_b, 0))

        painter.setBrush(QBrush(aura_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), aura_r, aura_r)

        # 2. Slender sleep crescent moon
        slender_r = r * 0.85
        full_moon = QPainterPath()
        full_moon.addEllipse(QPointF(cx - r * 0.1, cy), slender_r, slender_r)

        mask_moon = QPainterPath()
        mask_r = slender_r * 0.84
        mask_moon.addEllipse(QPointF(cx + r * 0.35, cy - r * 0.1), mask_r, mask_r)

        crescent = full_moon.subtracted(mask_moon)

        moon_grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        moon_grad.setColorAt(0.0, QColor(int(240 + warm_ratio * 15), int(245 + warm_ratio * 5), int(255 - warm_ratio * 20), 230))
        moon_grad.setColorAt(1.0, QColor(int(160 + warm_ratio * 50), int(175 + warm_ratio * 25), int(215 - warm_ratio * 40), 180))

        painter.setBrush(QBrush(moon_grad))
        painter.setPen(QPen(QColor(255, 255, 255, int(80 + 50 * pulse)), 0.6))
        painter.drawPath(crescent)

        # 3. Companion twinkling starlight dot
        star_x = cx + r * 0.45
        star_y = cy - r * 0.35
        star_r = 1.4 + 1.2 * pulse
        star_color = QColor(int(245 + warm_ratio * 10), int(245 + warm_ratio * 10), 255, int(160 + 95 * pulse))

        painter.setBrush(QBrush(star_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(star_x, star_y), star_r, star_r)
