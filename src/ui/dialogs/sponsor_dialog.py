"""Luna Dimmer - 开发者赞赏与全天候心意中心 (Sponsor & Circadian Care Sentinel)

设计哲学 (Apple Emotional Design):
1. 极致精炼与温暖：当用户点击打赏时，不展现冰冷的收款码与冗长文章，而是呈现一纸短小真挚的便签；
2. 全天候生物钟分时关怀 (Circadian Chronobiology 5-Phase Model):
   - 🌅 清晨/早上 (06:00 ~ 11:29): 晨光破晓，问候是否睡好，提醒先吃口热饭；
   - 🍱 中午/午休 (11:30 ~ 13:59): 办公室关灯，劝慰合上电脑闭目养神；
   - ☕ 困顿午后 (14:00 ~ 18:29): 阳光渐斜，递上一杯温茶，给心灵两分钟喘息；
   - 🌆 晚间加班 (18:30 ~ 23:29): 工位走空，劝慰忙完手头小事早点回家；
   - 🌙 凌晨熬夜 (23:30 ~ 05:59): 万籁俱寂，心疼发酸双眼，恳求立刻关机钻被窝睡觉。
3. 纯粹无废话：取消滚动条，精炼为一张拿在手心的精致温暖卡片 (480x370)。
"""

from typing import Optional
from datetime import datetime

from PyQt5.QtCore import Qt, QPoint, QRectF, QTimer
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QLinearGradient,
    QFont,
    QCursor,
)
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
    QApplication,
)

from src.i18n import t, get_language
from src.win32_compat import start_window_drag
from src.widgets.mac_controls import MacTrafficLights


def get_time_period() -> str:
    """获取当前时刻的昼夜生物钟心意时段"""
    now = datetime.now()
    m = now.hour * 60 + now.minute
    if 6 * 60 <= m < 11 * 60 + 30:
        return "morning"
    elif 11 * 60 + 30 <= m < 14 * 60:
        return "noon"
    elif 14 * 60 <= m < 18 * 60 + 30:
        return "afternoon"
    elif 18 * 60 + 30 <= m < 23 * 60 + 30:
        return "evening"
    else:
        return "midnight"


def is_late_night() -> bool:
    """判断当前时刻是否为夜深时段"""
    return get_time_period() in ("evening", "midnight")


class SponsorDialog(QDialog):
    """
    Apple macOS 原生风格开发者赞赏与陌生人心意短笺对话框
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(480, 370)

        self._period = get_time_period()
        self._theme = (
            getattr(parent, "current_theme", None)
            or getattr(parent, "selected_theme", None)
            or "dark"
        )
        self._init_ui()
        self.apply_theme(self._theme)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2,
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 顶部标题栏区域（<= 48px）支持平滑硬件加速拖动
            if event.pos().y() <= 48:
                start_window_drag(int(self.winId()))
                event.accept()
                return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(0)

        # 核心卡片容器 (Mac Inset Card)
        self.card = QFrame(self)
        self.card.setObjectName("sponsorCard")
        root_layout.addWidget(self.card)

        # 弥散柔和阴影
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 110))
        shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 1. 顶部 Header (左侧对称占位 + 居中标题 + 右侧控制按钮)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        left_placeholder = QWidget(self.card)
        left_placeholder.setFixedSize(28, 12)
        top_row.addWidget(left_placeholder)

        top_row.addStretch()

        title_text = t(f"sponsor_title_{self._period}", t("sponsor_title_day"))
        self.lbl_title = QLabel(title_text, self.card)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
        top_row.addWidget(self.lbl_title)

        top_row.addStretch()

        # 右侧：信号灯与关闭按钮
        self.traffic_lights = MacTrafficLights(self.card, reverse_order=True)
        self.traffic_lights.sig_min.connect(self.hide)
        self.traffic_lights.sig_close.connect(self.reject)
        top_row.addWidget(self.traffic_lights)

        layout.addLayout(top_row)

        # 2. 核心心意便签卡片 (精巧卡片，无需滚动条，一眼读完直击内心)
        self.letter_card = QFrame(self.card)
        self.letter_card.setObjectName("letterCard")
        lc_layout = QVBoxLayout(self.letter_card)
        lc_layout.setContentsMargins(18, 14, 18, 14)
        lc_layout.setSpacing(0)

        self.lbl_letter = QLabel(self.letter_card)
        self.lbl_letter.setTextFormat(Qt.RichText)
        self.lbl_letter.setWordWrap(True)
        self.lbl_letter.setStyleSheet("border: none; background: transparent;")
        self.lbl_letter.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.lbl_letter.setText(self._compose_letter_html())
        lc_layout.addWidget(self.lbl_letter)

        layout.addWidget(self.letter_card, 1)

        # 3. 底部操作栏 (左侧复制一份温暖 + 右侧主操作按钮)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(2, 2, 2, 0)
        btn_row.setSpacing(10)

        self.btn_copy = QPushButton(t("btn_sponsor_copy", "📋 复制这份温暖"), self.card)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setFixedHeight(34)
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        btn_row.addWidget(self.btn_copy)

        btn_row.addStretch()

        btn_main_text = t(f"btn_sponsor_close_{self._period}", t("btn_sponsor_close_day"))
        self.btn_main = QPushButton(btn_main_text, self.card)
        self.btn_main.setCursor(Qt.PointingHandCursor)
        self.btn_main.setFixedHeight(34)
        self.btn_main.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_main)

        layout.addLayout(btn_row)

    def apply_theme(self, theme: str):
        """根据当前系统主题（深色 / 浅色 / 液态玻璃）自适应高对比色彩"""
        self._theme = theme if theme in ("dark", "light", "liquid_glass") else "dark"
        if self._theme == "light":
            self.card.setStyleSheet("""
                QFrame#sponsorCard {
                    background: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 18px;
                }
                QLabel {
                    color: #1D1D1F;
                    font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei UI", "Segoe UI", sans-serif;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #1D1D1F; border: none; background: transparent;")
            self.letter_card.setStyleSheet("""
                QFrame#letterCard {
                    background: rgba(0, 0, 0, 0.035);
                    border: 1px solid rgba(0, 0, 0, 0.08);
                    border-left: 3px solid #0284C7;
                    border-radius: 12px;
                }
            """)
            self.btn_copy.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 8px;
                    padding: 0 14px;
                    color: #475569;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.09);
                    color: #1E293B;
                }
            """)
            self.btn_main.setStyleSheet("""
                QPushButton {
                    background: #0071E3;
                    border: none;
                    border-radius: 8px;
                    padding: 0 18px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0077ED;
                }
            """)
        elif self._theme == "liquid_glass":
            self.card.setStyleSheet("""
                QFrame#sponsorCard {
                    background: rgba(20, 22, 30, 0.94);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-top: 1.2px solid rgba(255, 255, 255, 0.38);
                    border-radius: 18px;
                }
                QLabel {
                    color: #FFFFFF;
                    font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei UI", "Segoe UI", sans-serif;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
            self.letter_card.setStyleSheet("""
                QFrame#letterCard {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-left: 3px solid #38BDF8;
                    border-radius: 12px;
                }
            """)
            self.btn_copy.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.16);
                    border-radius: 8px;
                    padding: 0 14px;
                    color: #E2E8F0;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.16);
                    color: #FFFFFF;
                }
            """)
            self.btn_main.setStyleSheet("""
                QPushButton {
                    background: #0A84FF;
                    border: none;
                    border-radius: 8px;
                    padding: 0 18px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0071E3;
                }
            """)
        else:  # Dark
            self.card.setStyleSheet("""
                QFrame#sponsorCard {
                    background: #1C1C1E;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 18px;
                }
                QLabel {
                    color: #FFFFFF;
                    font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei UI", "Segoe UI", sans-serif;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
            banner_border = {
                "morning": "#38BDF8",
                "noon": "#34D399",
                "afternoon": "#60A5FA",
                "evening": "#A78BFA",
                "midnight": "#818CF8",
            }.get(self._period, "#38BDF8")
            self.letter_card.setStyleSheet(f"""
                QFrame#letterCard {{
                    background: rgba(255, 255, 255, 0.035);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-left: 3px solid {banner_border};
                    border-radius: 12px;
                }}
            """)
            self.btn_copy.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 8px;
                    padding: 0 14px;
                    color: #CBD5E1;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                    color: #FFFFFF;
                }
            """)
            self.btn_main.setStyleSheet("""
                QPushButton {
                    background: #0A84FF;
                    border: none;
                    border-radius: 8px;
                    padding: 0 18px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0071E3;
                }
            """)

        if hasattr(self, "lbl_letter"):
            self.lbl_letter.setText(self._compose_letter_html())

    def _compose_letter_html(self) -> str:
        """生成短小温情、直击成年人心灵深处的暖心便签 (精炼 100~130 字，配生动 emoji)"""
        is_zh = (get_language() == "zh-CN")

        if is_zh:
            if self._period == "morning":
                html = """
                <div style="color: #CBD5E1; font-size: 13px; line-height: 22px;">
                    <p style="margin: 0 0 8px 0;">早安，朋友 ☀️！整座城市还在苏醒，而你已坐在了屏幕前。大人们都在催你赶路，而我只想轻声问一句：昨晚睡得好吗？🥺</p>
                    <p style="margin: 0 0 8px 0;"><span style="color: #38BDF8; font-weight: 700;">Luna Dimmer 永久 100% 免费，分文不取 🙅‍♂️。</span>做这款工具，只是想替你挡住刺眼的清晨冷光 💡。</p>
                    <p style="margin: 0; color: #94A3B8;">无论今天有多忙，先吃一口热腾腾的早餐 🥟。屏幕的光调柔和了，今天也请温柔对待自己 💛！</p>
                </div>
                """
            elif self._period == "noon":
                html = """
                <div style="color: #CBD5E1; font-size: 13px; line-height: 22px;">
                    <p style="margin: 0 0 8px 0;">大灯熄了，周围暗悄悄的，唯独你还在微光里敲着键盘，把所有疲倦咽进肚子里 🥺。</p>
                    <p style="margin: 0 0 8px 0;"><span style="color: #34D399; font-weight: 700;">Luna Dimmer 永久免费，拒绝打赏 🙅‍♂️。</span>请把钱留给自己中午吃顿好的 🍲。</p>
                    <p style="margin: 0; color: #94A3B8;">工作永远赶不完，但你只有一个。哪怕十分钟，合上电脑闭目小憩一会儿 💤，身体比手头的任务更宝贵 💛！</p>
                </div>
                """
            elif self._period == "afternoon":
                html = """
                <div style="color: #CBD5E1; font-size: 13px; line-height: 22px;">
                    <p style="margin: 0 0 8px 0;">日光渐斜，眼睛又干涩发酸了吧？成人的世界里，所有人都在问你飞得高不高，很少有人问你累不累 🥺。</p>
                    <p style="margin: 0 0 8px 0;"><span style="color: #60A5FA; font-weight: 700;">Luna Dimmer 纯粹免费，谢绝所有赞赏 🙅‍♂️。</span></p>
                    <p style="margin: 0; color: #94A3B8;">站起来，去接一杯温热的水 🍵，望一眼窗外的天和云 ☁️。你已经做得很棒了，给自己两分钟喘息，深呼吸吧 💛！</p>
                </div>
                """
            elif self._period == "evening":
                html = """
                <div style="color: #CBD5E1; font-size: 13px; line-height: 22px;">
                    <p style="margin: 0 0 8px 0;">街灯亮了，周围工位都空了，你是不是又默默撑到了最后 🥺？在万家灯火里独自消解疲惫，最让人心疼。</p>
                    <p style="margin: 0 0 8px 0;"><span style="color: #A78BFA; font-weight: 700;">Luna Dimmer 永久免费，坚决不收一分钱 🙅‍♂️。</span></p>
                    <p style="margin: 0; color: #94A3B8;">今天的仗你打赢了，收起电脑早点回家吧 🚶‍♂️！热腾腾的饭菜 🍲 和温暖的被窝 🛌 都在等你，辛苦了 💛！</p>
                </div>
                """
            else:  # midnight
                html = """
                <div style="color: #CBD5E1; font-size: 13px; line-height: 22px;">
                    <p style="margin: 0 0 8px 0;">夜深了，整座城市都睡了，唯独你的屏幕还亮在夜色里 🥺。成年人最大的破防，往往只因一句‘注意身体’。</p>
                    <p style="margin: 0 0 8px 0;"><span style="color: #818CF8; font-weight: 700;">请听陌生人最真诚的劝告：Luna Dimmer 永久免费，分文不取 🙅‍♂️。</span></p>
                    <p style="margin: 0; color: #94A3B8;">屏幕再柔和也换不来健康。今晚你不用向任何人证明什么，关掉屏幕，去被窝里睡个好觉吧 🌙💛！</p>
                </div>
                """
        else:
            html = """
            <div style="color: #CBD5E1; font-size: 13px; line-height: 22px;">
                <p style="margin: 0 0 8px 0;">The world always demands results, but I just want to ask: are you tired today? 🥺</p>
                <p style="margin: 0 0 8px 0;"><span style="color: #38BDF8; font-weight: 700;">Luna Dimmer is 100% free forever and declines all tips 🙅‍♂️.</span> We built this to shield your tired eyes from glare 💡.</p>
                <p style="margin: 0; color: #94A3B8;">Tasks never end, but your health is irreplaceable. Grab a warm drink 🍵 and get some rest. You've fought hard—be gentle with yourself tonight 💛!</p>
            </div>
            """

        if getattr(self, "_theme", "dark") == "light":
            html = html.replace("#CBD5E1", "#334155")
            html = html.replace("#94A3B8", "#64748B")
            html = html.replace("#FFFFFF", "#0F172A")
        return html

    def _get_plain_letter_text(self) -> str:
        """获取纯文本版本的暖心短信（用于一键复制分享）"""
        if get_language() == "zh-CN":
            quotes = {
                "morning": "早安，朋友 ☀️！整座城市还在苏醒，而你已坐在了屏幕前。大人们都在催你赶路，而我只想轻声问一句：昨晚睡得好吗？🥺\nLuna Dimmer 永久 100% 免费，分文不取。无论今天有多忙，先吃一口热腾腾的早餐 🥟，今天也请温柔对待自己 💛！\n—— 来自为你加油的陌生人",
                "noon": "大灯熄了，周围暗悄悄的，唯独你还在微光里敲着键盘，把所有疲倦咽进肚子里 🥺。\nLuna Dimmer 永久免费，拒绝所有打赏。工作永远赶不完，但你只有一个。哪怕十分钟，合上电脑闭目小憩一会儿 💤，身体比手头的任务更宝贵 💛！\n—— 劝你歇一歇的陌生人",
                "afternoon": "日光渐斜，眼睛又干涩发酸了吧？成人的世界里，所有人都在问你飞得高不高，很少有人问你累不累 🥺。\nLuna Dimmer 纯粹免费，谢绝所有赞赏。站起来，去接一杯温热的水 🍵，望一眼窗外的天和云 ☁️。你已经做得很棒了，给自己两分钟喘息，深呼吸吧 💛！\n—— 陪你度过午后的陌生人",
                "evening": "街灯亮了，周围工位都空了，你是不是又默默撑到了最后 🥺？在万家灯火里独自消解疲惫，最让人心疼。\nLuna Dimmer 永久免费，坚决不收一分钱。今天的仗你打赢了，收起电脑早点回家吧 🚶‍♂️！热腾腾的饭菜 🍲 和温暖的被窝 🛌 都在等你，辛苦了 💛！\n—— 愿你早点到家的陌生人",
                "midnight": "夜深了，整座城市都睡了，唯独你的屏幕还亮在夜色里 🥺。成年人最大的破防，往往只因一句‘注意身体’。\n请听陌生人最真诚的劝告：Luna Dimmer 永久免费，分文不取。屏幕再柔和也换不来健康。今晚你不用向任何人证明什么，关掉屏幕，去被窝里睡个好觉吧 🌙💛！\n—— 深夜里心疼你的陌生人",
            }
            return quotes.get(self._period, quotes["midnight"])
        else:
            return (
                "The world always demands results, but I just want to ask: are you tired today? 🥺\n"
                "Luna Dimmer is 100% free forever and declines all tips 🙅‍♂️.\n"
                "Tasks never end, but your health is irreplaceable. Grab a warm drink 🍵, have a good meal 🍲, and get some rest. You've fought hard—be gentle with yourself tonight 💛!\n"
                "— From a stranger quietly rooting for you"
            )

    def _on_copy_clicked(self):
        """一键复制暖心短笺到系统剪贴板"""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self._get_plain_letter_text())
        self.btn_copy.setText(t("btn_sponsor_copied", "✓ 已复制这份温暖"))
        QTimer.singleShot(2500, lambda: self.btn_copy.setText(t("btn_sponsor_copy", "📋 复制这份温暖")))
