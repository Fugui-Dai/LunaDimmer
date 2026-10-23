# -*- coding: utf-8 -*-
"""Luna Dimmer - 苹果灵动微缩胶囊 HUD (macOS Dynamic Island Luminary HUD)

当用户通过全局快捷键（如 Ctrl+Alt+Up / Down）在全屏游戏、观影或工作盲操调光时，
或切换场景预设、微光聚光灯时，在屏幕顶部中央优雅滑出微缩磨砂黑胶囊，提供平滑视觉反馈，
具备 100% 鼠标点击穿透与零窗口焦点抢占（WS_EX_TRANSPARENT | WS_EX_NOACTIVATE）。
"""

from typing import Optional
from PyQt5.QtCore import Qt, QPoint, QRectF, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QFont, QCursor
from PyQt5.QtWidgets import QWidget, QApplication

from src.win32_compat import set_window_transparent_clickthrough


class LuminaryHUD(QWidget):
    """
    macOS 风格深空磨砂微缩胶囊调光 HUD (Dynamic Floating Capsule)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._value = 100
        self._icon = "☀️"
        self._title = "亮度"
        self._accent_mode = "brightness"  # "brightness" | "warmth"

        self._is_notice = False
        self._notice_title = ""
        self._notice_subtitle = ""

        self._opacity = 0.0
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(1200)
        self._hide_timer.timeout.connect(self._fade_out)

        # 全生命周期单例动画引擎，杜绝高频触发创建废弃 QPropertyAnimation 对象产生内存泄漏
        self._anim_fade = QPropertyAnimation(self, b"opacity", self)

        self._setup_window()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(220, 48)

    # Qt Property for smooth opacity animation
    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, val: float):
        self._opacity = val
        self.setWindowOpacity(val)
        self.update()

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def show_value(self, value: int, accent_mode: str = "brightness"):
        """激活并展示当前调光数值 (附带平滑位置居中与自动延时淡出)"""
        self._is_notice = False
        self.setFixedSize(220, 48)
        self._value = max(0, min(100, int(value)))
        self._accent_mode = accent_mode
        self._icon = "☀️" if accent_mode == "brightness" else "🕯️"

        # 定位在当前活动屏幕中上方
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            target_x = avail.x() + (avail.width() - self.width()) // 2
            target_y = avail.y() + 28  # 黄金下沉 28px
            self.move(target_x, target_y)

        # 确保穿透与无焦点
        if not self.isVisible():
            self.show()
            try:
                set_window_transparent_clickthrough(int(self.winId()))
            except Exception:
                pass

        # 启动渐现动画（复用单例引擎）
        if self._anim_fade.state() == QPropertyAnimation.Running:
            self._anim_fade.stop()
        try:
            self._anim_fade.finished.disconnect()
        except Exception:
            pass

        self._anim_fade.setDuration(160)
        self._anim_fade.setStartValue(self._opacity)
        self._anim_fade.setEndValue(1.0)
        self._anim_fade.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_fade.start()

        self.update()
        self._hide_timer.setInterval(1200)
        self._hide_timer.start()

    def show_notice(self, title: str, subtitle: str = ""):
        """激活并展示状态通知胶囊 (如常用预设切换、快捷键通知)"""
        self._is_notice = True
        self._notice_title = str(title)
        self._notice_subtitle = str(subtitle)

        # 动态自适应胶囊尺寸：根据文本长度智能拓宽
        max_len = max(len(self._notice_title), len(self._notice_subtitle))
        calc_width = max(240, min(380, 190 + max_len * 9))
        self.setFixedSize(calc_width, 48)

        # 定位在当前活动屏幕中上方
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            target_x = avail.x() + (avail.width() - self.width()) // 2
            target_y = avail.y() + 28  # 黄金下沉 28px
            self.move(target_x, target_y)

        # 确保穿透与无焦点
        if not self.isVisible():
            self.show()
            try:
                set_window_transparent_clickthrough(int(self.winId()))
            except Exception:
                pass

        # 启动渐现动画（复用单例引擎）
        if self._anim_fade.state() == QPropertyAnimation.Running:
            self._anim_fade.stop()
        try:
            self._anim_fade.finished.disconnect()
        except Exception:
            pass

        self._anim_fade.setDuration(160)
        self._anim_fade.setStartValue(self._opacity)
        self._anim_fade.setEndValue(1.0)
        self._anim_fade.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_fade.start()

        self.update()
        self._hide_timer.setInterval(1600)  # 通知停留 1.6 秒
        self._hide_timer.start()

    def _fade_out(self):
        if self._anim_fade.state() == QPropertyAnimation.Running:
            self._anim_fade.stop()
        try:
            self._anim_fade.finished.disconnect()
        except Exception:
            pass

        self._anim_fade.setDuration(300)
        self._anim_fade.setStartValue(self._opacity)
        self._anim_fade.setEndValue(0.0)
        self._anim_fade.setEasingCurve(QEasingCurve.InCubic)
        self._anim_fade.finished.connect(self.hide)
        self._anim_fade.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect())

        # 1. 超椭圆深空暗夜磨砂背景 (rgba(18, 20, 26, 0.94))
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, 24, 24)

        painter.fillPath(bg_path, QColor(18, 20, 26, 240))

        # 顶部 0.5px 精细高光 (Rim Light)
        painter.setPen(QColor(255, 255, 255, 38))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 23.5, 23.5)

        # 2. 如果是通知模式，绘制标题与副标题
        if self._is_notice:
            if self._notice_subtitle:
                painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
                painter.setPen(QColor(245, 248, 255))
                painter.drawText(
                    QRectF(16, 7, rect.width() - 32, 18),
                    Qt.AlignCenter,
                    self._notice_title,
                )
                painter.setFont(QFont("Segoe UI", 9))
                painter.setPen(QColor(148, 163, 184))
                painter.drawText(
                    QRectF(16, 25, rect.width() - 32, 16),
                    Qt.AlignCenter,
                    self._notice_subtitle,
                )
            else:
                painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
                painter.setPen(QColor(245, 248, 255))
                painter.drawText(
                    QRectF(16, 0, rect.width() - 32, rect.height()),
                    Qt.AlignCenter,
                    self._notice_title,
                )
            return

        # 3. 调光数值模式：左侧拟态图标
        painter.setFont(QFont("Segoe UI Emoji", 12))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(14, 0, 24, rect.height()), Qt.AlignCenter, self._icon)

        # 中间微缩进度滑道
        track_x = 44.0
        track_y = 20.0
        track_w = 118.0
        track_h = 8.0
        track_rect = QRectF(track_x, track_y, track_w, track_h)

        # 滑道底色
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 25))
        painter.drawRoundedRect(track_rect, 4, 4)

        # 进度填充
        fill_w = max(4.0, track_w * (self._value / 100.0))
        fill_rect = QRectF(track_x, track_y, fill_w, track_h)

        if self._accent_mode == "warmth":
            grad = QLinearGradient(track_x, 0, track_x + fill_w, 0)
            grad.setColorAt(0.0, QColor(255, 215, 110))
            grad.setColorAt(1.0, QColor(230, 115, 20))
            painter.setBrush(grad)
        else:
            grad = QLinearGradient(track_x, 0, track_x + fill_w, 0)
            grad.setColorAt(0.0, QColor(255, 255, 255))
            grad.setColorAt(1.0, QColor(205, 210, 225))
            painter.setBrush(grad)

        painter.drawRoundedRect(fill_rect, 4, 4)

        # 右侧等宽排版百分比文本
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.setPen(QColor(235, 240, 250, 220))
        val_text = f"{self._value}%"
        painter.drawText(QRectF(166, 0, 44, rect.height()), Qt.AlignVCenter | Qt.AlignLeft, val_text)
