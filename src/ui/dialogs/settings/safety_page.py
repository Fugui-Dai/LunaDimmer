"""Luna Dimmer - 设置中心：安全与重置分页 (Safety & Reset Page)

包含：
1. 纯净无痕运行声明卡片 (零残留、不改注册表)；
2. 恢复软件出厂默认设置卡片 (高危操作 MacConfirmDialog 模态确认拦截)；
3. 体验与问题反馈入口 (FeedbackDialog)；
4. 开发者赞赏与夜深守候心意入口 (SponsorDialog)。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QDialog,
)

from src.i18n import t
from src.sponsor_dialog import get_time_period
from src.widgets.mac_controls import (
    MacInsetCard,
    MacSettingRow,
    MacConfirmDialog,
)


class SafetyPage(QWidget):
    """安全守护、出厂重置与开发者连接设置页面"""

    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog
        self.config = parent_dialog.config
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 3.1 纯净无痕声明卡片 (Inset Grouped Squircle Card)
        self.card_safety = MacInsetCard(self)
        safety_box = QWidget(self.card_safety)
        box_layout = QVBoxLayout(safety_box)
        box_layout.setContentsMargins(14, 14, 14, 14)
        box_layout.setSpacing(8)

        # 头部绿色圆角微晶胶囊徽标 (Apple 12px Pill Capsule Badge)
        self.lbl_safe_title = QLabel("🛡️ " + t("safety_title"), safety_box)
        self.lbl_safe_title.setFixedHeight(24)
        self.lbl_safe_title.setStyleSheet("""
            QLabel {
                background: rgba(52, 211, 153, 0.14);
                border: 1px solid rgba(52, 211, 153, 0.35);
                border-radius: 12px;
                padding: 2px 10px;
                font-size: 12.5px;
                font-weight: 700;
                color: #34D399;
            }
        """)
        box_layout.addWidget(self.lbl_safe_title, 0, Qt.AlignLeft)

        self.lbl_safe_note = QLabel(t("safety_note"), safety_box)
        self.lbl_safe_note.setWordWrap(True)
        self.lbl_safe_note.setStyleSheet("font-size: 12px; font-weight: 400; color: #94A3B8; line-height: 16px;")
        box_layout.addWidget(self.lbl_safe_note)

        self.card_safety.card_layout.addWidget(safety_box)
        layout.addWidget(self.card_safety)

        # 3.2 恢复出厂设置卡片 (Apple Destructive Action)
        self.card_reset = MacInsetCard(self)
        self.btn_reset = QPushButton(t("btn_restore_defaults"), self.card_reset)
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setFixedHeight(30)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.38);
                border-radius: 8px;
                padding: 4px 16px;
                color: #F87171;
                font-size: 12.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.24);
                border-color: #EF4444;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: rgba(185, 28, 28, 0.40);
            }
        """)
        self.btn_reset.clicked.connect(self.prompt_restore_defaults)

        self.row_reset = MacSettingRow(
            t("btn_restore_defaults"),
            t("reset_restore_sub"),
            self.btn_reset,
            is_last=True,
            parent=self.card_reset,
        )
        self.card_reset.add_row(self.row_reset)

        # 3.3 体验与问题反馈卡片
        self.card_fb = MacInsetCard(self)
        self.btn_open_feedback = QPushButton(t("btn_open_feedback"), self.card_fb)
        self.btn_open_feedback.setCursor(Qt.PointingHandCursor)
        self.btn_open_feedback.setFixedHeight(30)
        self.btn_open_feedback.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.12);
                border: 1px solid rgba(56, 189, 248, 0.38);
                border-radius: 8px;
                padding: 4px 16px;
                color: #38BDF8;
                font-size: 12.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.24);
                border-color: #38BDF8;
                color: #FFFFFF;
            }
        """)
        self.btn_open_feedback.clicked.connect(self._open_feedback)

        self.row_fb = MacSettingRow(
            t("feedback_title"),
            t("feedback_sub"),
            self.btn_open_feedback,
            is_last=True,
            parent=self.card_fb,
        )
        self.card_fb.add_row(self.row_fb)
        layout.addWidget(self.card_fb)

        # 3.4 开发者赞赏与守候卡片
        self.card_sponsor = MacInsetCard(self)
        self.btn_open_sponsor = QPushButton(t("btn_open_sponsor"), self.card_sponsor)
        self.btn_open_sponsor.setCursor(Qt.PointingHandCursor)
        self.btn_open_sponsor.setFixedHeight(30)
        self.btn_open_sponsor.setStyleSheet("""
            QPushButton {
                background: rgba(167, 139, 250, 0.12);
                border: 1px solid rgba(167, 139, 250, 0.38);
                border-radius: 8px;
                padding: 4px 16px;
                color: #A78BFA;
                font-size: 12.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(167, 139, 250, 0.24);
                border-color: #A78BFA;
                color: #FFFFFF;
            }
        """)
        self.btn_open_sponsor.clicked.connect(self._open_sponsor)

        period = get_time_period()
        self.row_sponsor = MacSettingRow(
            t("sponsor_pref_title"),
            t(f"sponsor_sub_{period}", t("sponsor_pref_sub")),
            self.btn_open_sponsor,
            is_last=True,
            parent=self.card_sponsor,
        )
        self.card_sponsor.add_row(self.row_sponsor)
        layout.addWidget(self.card_sponsor)

        # 恢复出厂设置卡片置于底部 (Apple Destructive Action at Bottom)
        layout.addWidget(self.card_reset)

        layout.addStretch()

    def prompt_restore_defaults(self):
        """唤出恢复出厂设置危险操作二次确认对话框 (Mac Sheet 模态拦截)"""
        theme = self.config.get("theme", "dark")
        bullets = [
            t("reset_confirm_bullet_hotkeys", "全部全局快捷键恢复为默认初始键位"),
            t("reset_confirm_bullet_presets", "6 项常用场景预设（含自定义预设）恢复出厂数值"),
            t("reset_confirm_bullet_prefs", "开机自启、窗口记忆与平滑过渡偏好恢复初始状态"),
            t("reset_confirm_bullet_theme", "外观主题恢复为深色，界面语言恢复为简体中文"),
        ]

        dlg = MacConfirmDialog(
            title=t("reset_confirm_title", "恢复软件出厂默认设置？"),
            desc=t("reset_confirm_desc", "此操作属于危险操作，执行后将清除所有个性化偏好且无法撤销："),
            details=bullets,
            confirm_text=t("reset_confirm_ok", "确定恢复出厂设置"),
            cancel_text=t("reset_confirm_cancel", "取消"),
            is_destructive=True,
            theme=theme,
            parent=self.parent_dialog,
        )

        if dlg.exec_() == QDialog.Accepted:
            self.parent_dialog._do_restore_defaults()

    def _open_feedback(self):
        from src.feedback_dialog import FeedbackDialog
        dlg = FeedbackDialog(parent=self.parent_dialog)
        dlg.exec_()

    def _open_sponsor(self):
        from src.sponsor_dialog import SponsorDialog
        dlg = SponsorDialog(parent=self.parent_dialog)
        dlg.exec_()

    def apply_theme(self, theme: str):
        for card in [self.card_safety, self.card_reset, self.card_fb, self.card_sponsor]:
            card.apply_theme(theme)

        period = get_time_period()
        self.row_sponsor.lbl_sub.setText(t(f"sponsor_sub_{period}", t("sponsor_pref_sub")))

        if theme == "light":
            self.lbl_safe_title.setStyleSheet("""
                QLabel {
                    background: rgba(36, 138, 61, 0.10);
                    border: 1px solid rgba(36, 138, 61, 0.28);
                    border-radius: 12px;
                    padding: 2px 10px;
                    font-size: 12.5px;
                    font-weight: 700;
                    color: #248A3D;
                }
            """)
            self.lbl_safe_note.setStyleSheet("font-size: 12px; font-weight: 400; color: rgba(60, 60, 67, 0.70); line-height: 16px;")
            self.btn_reset.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 59, 48, 0.08);
                    border: 1px solid rgba(255, 59, 48, 0.28);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #FF3B30;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 59, 48, 0.16);
                    border-color: #FF3B30;
                    color: #FF3B30;
                }
                QPushButton:pressed {
                    background: rgba(255, 59, 48, 0.24);
                }
            """)
            self.btn_open_feedback.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 122, 255, 0.08);
                    border: 1px solid rgba(0, 122, 255, 0.28);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #007AFF;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(0, 122, 255, 0.16);
                    border-color: #007AFF;
                    color: #007AFF;
                }
                QPushButton:pressed {
                    background: rgba(0, 122, 255, 0.24);
                }
            """)
            self.btn_open_sponsor.setStyleSheet("""
                QPushButton {
                    background: rgba(139, 92, 246, 0.08);
                    border: 1px solid rgba(139, 92, 246, 0.28);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #7C3AED;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(139, 92, 246, 0.16);
                    border-color: #7C3AED;
                    color: #7C3AED;
                }
                QPushButton:pressed {
                    background: rgba(139, 92, 246, 0.24);
                }
            """)
        elif theme == "liquid_glass":
            self.lbl_safe_title.setStyleSheet("""
                QLabel {
                    background: rgba(48, 209, 88, 0.18);
                    border: 1px solid rgba(48, 209, 88, 0.40);
                    border-radius: 12px;
                    padding: 2px 10px;
                    font-size: 12.5px;
                    font-weight: 700;
                    color: #30D158;
                }
            """)
            self.lbl_safe_note.setStyleSheet("font-size: 12px; font-weight: 400; color: rgba(235, 235, 245, 0.70); line-height: 16px;")
            self.btn_reset.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 69, 58, 0.16);
                    border: 1px solid rgba(255, 69, 58, 0.40);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #FF453A;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 69, 58, 0.28);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(255, 69, 58, 0.36);
                }
            """)
            self.btn_open_feedback.setStyleSheet("""
                QPushButton {
                    background: rgba(10, 132, 255, 0.16);
                    border: 1px solid rgba(10, 132, 255, 0.40);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #0A84FF;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(10, 132, 255, 0.28);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(10, 132, 255, 0.36);
                }
            """)
            self.btn_open_sponsor.setStyleSheet("""
                QPushButton {
                    background: rgba(167, 139, 250, 0.16);
                    border: 1px solid rgba(167, 139, 250, 0.40);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #C4B5FD;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(167, 139, 250, 0.28);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(167, 139, 250, 0.36);
                }
            """)
        else:
            self.lbl_safe_title.setStyleSheet("""
                QLabel {
                    background: rgba(52, 211, 153, 0.14);
                    border: 1px solid rgba(52, 211, 153, 0.35);
                    border-radius: 12px;
                    padding: 2px 10px;
                    font-size: 12.5px;
                    font-weight: 700;
                    color: #34D399;
                }
            """)
            self.lbl_safe_note.setStyleSheet("font-size: 12px; font-weight: 400; color: rgba(235, 235, 245, 0.60); line-height: 16px;")
            self.btn_reset.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 69, 58, 0.12);
                    border: 1px solid rgba(255, 69, 58, 0.35);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #FF453A;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 69, 58, 0.24);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(255, 69, 58, 0.32);
                }
            """)
            self.btn_open_feedback.setStyleSheet("""
                QPushButton {
                    background: rgba(10, 132, 255, 0.12);
                    border: 1px solid rgba(10, 132, 255, 0.35);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #0A84FF;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(10, 132, 255, 0.24);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(10, 132, 255, 0.32);
                }
            """)
            self.btn_open_sponsor.setStyleSheet("""
                QPushButton {
                    background: rgba(167, 139, 250, 0.12);
                    border: 1px solid rgba(167, 139, 250, 0.38);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #A78BFA;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(167, 139, 250, 0.24);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(167, 139, 250, 0.34);
                }
            """)

    def retranslate(self):
        self.lbl_safe_title.setText("🛡️ " + t("safety_title"))
        self.lbl_safe_note.setText(t("safety_note"))
        self.row_reset.lbl_title.setText(t("btn_restore_defaults"))
        self.row_reset.lbl_sub.setText(t("reset_restore_sub"))
        self.btn_reset.setText(t("btn_restore_defaults"))
        self.row_fb.lbl_title.setText(t("feedback_title"))
        self.row_fb.lbl_sub.setText(t("feedback_sub"))
        self.btn_open_feedback.setText(t("btn_open_feedback"))
        self.row_sponsor.lbl_title.setText(t("sponsor_pref_title"))
        period = get_time_period()
        self.row_sponsor.lbl_sub.setText(t(f"sponsor_sub_{period}", t("sponsor_pref_sub")))
        self.btn_open_sponsor.setText(t("btn_open_sponsor"))
