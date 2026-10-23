"""Luna Dimmer - 设置中心：调光与护眼分页 (Optics Page)

包含：
1. DDC/CI I2C 物理硬件通道握手状态；
2. 息屏唤醒平滑贝塞尔过渡 (Anti-glare Bezier Smoothing)。
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from src.i18n import t
from src.widgets.mac_controls import (
    MacSwitch,
    MacInsetCard,
    MacSettingRow,
)


class OpticsPage(QWidget):
    """调光与光学护眼偏好设置页面"""

    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog
        self.config = parent_dialog.config
        self._init_ui()

    def _has_hardware_support(self) -> bool:
        """读取引擎真实探测结果：DDC/CI 是否可用（绝不再无条件显示绿灯）"""
        parent = self.parent_dialog.parent() if self.parent_dialog else None
        engine = getattr(parent, "engine", None)
        return bool(getattr(engine, "has_hardware_support", False))

    def _hw_status_text(self) -> str:
        return t("hw_ready") if self._has_hardware_support() else t("hw_soft")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1.1 硬件通信通道卡片
        self.card_hw = MacInsetCard(self)
        self.lbl_hw_status = QLabel(self._hw_status_text(), self.card_hw)
        self.lbl_hw_status.setWordWrap(True)
        self.lbl_hw_status.setStyleSheet("""
            QLabel {
                background: rgba(52, 211, 153, 0.12);
                border: 1px solid rgba(52, 211, 153, 0.35);
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 12.5px;
                font-weight: 600;
                color: #34D399;
            }
        """)
        self.row_hw = MacSettingRow(
            t("hw_channel"),
            t("hw_sub"),
            self.lbl_hw_status,
            is_last=True,
            parent=self.card_hw,
        )
        self.card_hw.add_row(self.row_hw)
        layout.addWidget(self.card_hw)

        # 1.2 护眼平滑调优卡片
        self.card_optics = MacInsetCard(self)
        self.stealth_bezier_switch = MacSwitch(self.card_optics)
        self.stealth_bezier_switch.setChecked(bool(self.config.get("smooth_wake", True)))
        self.stealth_bezier_switch.toggled.connect(
            lambda val: (self.config.set("smooth_wake", val), self.config.save())
        )

        self.row_stealth = MacSettingRow(
            t("stealth_wake"),
            t("stealth_wake_sub"),
            self.stealth_bezier_switch,
            is_last=True,
            parent=self.card_optics,
        )
        self.card_optics.add_row(self.row_stealth)
        layout.addWidget(self.card_optics)

        layout.addStretch()

    def apply_theme(self, theme: str):
        self.card_hw.apply_theme(theme)
        self.card_optics.apply_theme(theme)
        self.stealth_bezier_switch.update()
        self.lbl_hw_status.setText(self._hw_status_text())
        if theme == "light":
            self.lbl_hw_status.setStyleSheet("""
                QLabel {
                    background: rgba(52, 199, 89, 0.12);
                    border: 1px solid rgba(52, 199, 89, 0.28);
                    border-radius: 6px;
                    padding: 3px 10px;
                    font-size: 12.5px;
                    font-weight: 600;
                    color: #248A3D;
                }
            """)
        else:
            self.lbl_hw_status.setStyleSheet("""
                QLabel {
                    background: rgba(48, 209, 88, 0.15);
                    border: 1px solid rgba(48, 209, 88, 0.35);
                    border-radius: 6px;
                    padding: 3px 10px;
                    font-size: 12.5px;
                    font-weight: 600;
                    color: #30D158;
                }
            """)

    def retranslate(self):
        self.row_hw.lbl_title.setText(t("hw_channel"))
        self.row_hw.lbl_sub.setText(t("hw_sub"))
        self.lbl_hw_status.setText(self._hw_status_text())
        self.row_stealth.lbl_title.setText(t("stealth_wake"))
        self.row_stealth.lbl_sub.setText(t("stealth_wake_sub"))
