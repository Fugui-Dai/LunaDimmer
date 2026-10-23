"""Luna Dimmer - 官方应用图标绘制 (Shared Application Icon)

单一真相源：主窗口任务栏图标与系统托盘图标共用同一份绘制逻辑，
统一优先加载官方 assets/icon.png，缺失时通过高质矢量自绘兜底。
"""

import os
import sys
from typing import Optional

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap, QLinearGradient, QPen, QBrush


def _draw_vector_icon(size: int = 32) -> QIcon:
    """
    备用矢量兜底绘制：按全新 Luna 品牌图标（深蓝星空圆角微晶 + 金色弯月 + 内部刻度轮盘 + 阴阳光芒核心）自绘。
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    try:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 1. 深蓝渐变超椭圆圆角底座 (Squircle)
        bg_path = QPainterPath()
        r = size * 0.223
        bg_path.addRoundedRect(QRectF(1, 1, size - 2, size - 2), r, r)

        grad = QLinearGradient(0, 0, 0, size)
        grad.setColorAt(0.0, QColor(32, 60, 110))
        grad.setColorAt(1.0, QColor(14, 20, 38))
        painter.fillPath(bg_path, grad)

        # 细微高光边缘
        pen = QPen(QColor(80, 120, 180, 140), 1.0)
        painter.strokePath(bg_path, pen)

        # 2. 明亮金色弯月 (Crescent Moon)
        moon_path = QPainterPath()
        moon_path.addEllipse(QRectF(size * 0.16, size * 0.16, size * 0.68, size * 0.68))
        sub_path = QPainterPath()
        sub_path.addEllipse(QRectF(size * 0.30, size * 0.14, size * 0.60, size * 0.60))
        crescent = moon_path.subtracted(sub_path)

        moon_grad = QLinearGradient(size * 0.2, size * 0.2, size * 0.8, size * 0.8)
        moon_grad.setColorAt(0.0, QColor(255, 245, 220))
        moon_grad.setColorAt(1.0, QColor(240, 180, 100))
        painter.fillPath(crescent, moon_grad)

        # 3. 内部刻度轮盘
        cx, cy = size * 0.53, size * 0.50
        dial_r = size * 0.24
        painter.setPen(QPen(QColor(240, 200, 120, 160), 1.0))
        painter.setBrush(QColor(18, 24, 42, 200))
        painter.drawEllipse(QPointF(cx, cy), dial_r, dial_r)

        # 4. 中心阴阳光芒核心 (Half-Sun Core)
        sun_r = size * 0.08
        # 左半边深色
        dark_half = QPainterPath()
        dark_half.arcMoveTo(QRectF(cx - sun_r, cy - sun_r, sun_r * 2, sun_r * 2), 90)
        dark_half.arcTo(QRectF(cx - sun_r, cy - sun_r, sun_r * 2, sun_r * 2), 90, 180)
        dark_half.closeSubpath()
        painter.fillPath(dark_half, QColor(100, 100, 120))

        # 右半边亮色
        light_half = QPainterPath()
        light_half.arcMoveTo(QRectF(cx - sun_r, cy - sun_r, sun_r * 2, sun_r * 2), 270)
        light_half.arcTo(QRectF(cx - sun_r, cy - sun_r, sun_r * 2, sun_r * 2), 270, 180)
        light_half.closeSubpath()
        painter.fillPath(light_half, QColor(255, 248, 220))
    finally:
        painter.end()

    return QIcon(pixmap)


def load_app_icon(fallback_size: int = 32) -> QIcon:
    """优先加载打包资源 `assets/icon.png` 或 `assets/icon.ico`，缺失时回退到矢量自绘"""
    candidates = []
    base_dir = getattr(sys, "_MEIPASS", None)
    if base_dir:
        candidates.append(os.path.join(base_dir, "assets", "icon.png"))
        candidates.append(os.path.join(base_dir, "assets", "icon.ico"))

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidates.append(os.path.join(project_root, "assets", "icon.png"))
    candidates.append(os.path.join(project_root, "assets", "icon.ico"))

    for path in candidates:
        try:
            if os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    return icon
        except Exception:
            continue
    return _draw_vector_icon(fallback_size)


def create_app_icon(size: int = 32) -> QIcon:
    """获取应用程序全局官方图标（优先加载官方资源 assets/icon.png，缺失时自动矢量兜底）"""
    return load_app_icon(fallback_size=size)


def create_app_pixmap(size: int = 32) -> QPixmap:
    """返回图标位图本体（供需要 QPixmap 的场景复用）"""
    return create_app_icon(size).pixmap(size, size)


def create_tray_icon() -> QIcon:
    """托盘图标：优先使用官方 assets/icon.png，保证与全系统视觉一致"""
    return load_app_icon()


__all__ = ["create_app_icon", "create_app_pixmap", "load_app_icon", "create_tray_icon"]
