"""Luna Dimmer - 常用场景预设可视化自定义与管理中心 (PresetCustomizerDialog)

设计哲学 (Apple Emotional & Functional Design):
1. 提供媲美 macOS Ventura / Sonoma 的轻质感微晶毛玻璃编辑面板；
2. 支持对全部 6 大情境预设（白天办公、夜间阅读、睡前极暗、午间休息、自定义1、自定义2）进行全维度自定义：
   - 预设显示名称
   - 屏幕亮度百分比 (1% ~ 100%)
   - 护眼色温百分比 (0% ~ 100%)
   - 深度压暗微透镜开关 (2x Boost)
3. 贴心快捷功能：
   - 「📍 抓取当前屏幕参数」：所见即所得，一键将当前屏幕调好的状态填入；
   - 「👁️ 实时预览」：调节滑块时可即时在屏幕上感受真实光感；
   - 「↺ 恢复默认」：一键还原出厂官方调校预设。
"""

import copy
from typing import Optional, Dict, Any

from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtGui import (
    QColor,
    QPainter,
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
    QLineEdit,
    QSlider,
    QGraphicsDropShadowEffect,
    QApplication,
)

from src.i18n import t
from src.win32_compat import start_window_drag
from src.widgets.mac_controls import (
    MacTrafficLights,
    MacInsetCard,
    MacSettingRow,
    MacSwitch,
    MacSegmentedControl,
)
from src.config import DEFAULT_SCENE_PRESETS


class PresetCustomizerDialog(QDialog):
    """
    常用场景预设自定义与管理对话框 (macOS Ventura / Sonoma 质感)
    """

    def __init__(self, config, engine, parent: Optional[QWidget] = None, initial_preset_key: str = "custom_1"):
        super().__init__(parent)
        self.config = config
        self.engine = engine
        self.parent_window = parent

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(510, 520)

        # 本地暂存的编辑副本（缺失项自动回填出厂值，单一读取入口）
        self._presets_cache: Dict[str, Any] = self.config.get_scene_presets()

        self._active_key = initial_preset_key if initial_preset_key in self._presets_cache else "custom_1"
        self._theme = getattr(parent, "current_theme", "dark") if parent else "dark"

        # 记录打开弹窗时的屏幕初始状态（用于取消时恢复）
        self._initial_screen_b = self.engine.current_brightness
        self._initial_screen_w = self.engine.current_warmth
        self._initial_screen_boost = getattr(self.engine, "enhanced_2x", False)

        self._init_ui()
        self._load_preset_to_ui(self._active_key)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() <= 48:
            start_window_drag(int(self.winId()))
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(0)

        # 核心毛玻璃卡片
        self.card = QFrame(self)
        self.card.setObjectName("presetDialogCard")
        root_layout.addWidget(self.card)

        # 柔和抗锯齿弥散阴影
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 2)
        self.card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 1. 顶部 Header (标题 + 控制红绿灯)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(t("preset_dlg_title"), self.card)
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; border: none; background: transparent;")
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()

        self.traffic_lights = MacTrafficLights(self.card, reverse_order=True)
        self.traffic_lights.sig_min.connect(self.hide)
        self.traffic_lights.sig_close.connect(self._on_cancel_clicked)
        top_row.addWidget(self.traffic_lights)
        layout.addLayout(top_row)

        # 2. 预设选择器分段胶囊 (6 大情境)
        items = [
            ("work", t("preset_dlg_tab_work")),
            ("night", t("preset_dlg_tab_night")),
            ("sleep", t("preset_dlg_tab_sleep")),
            ("noon", t("preset_dlg_tab_noon")),
            ("custom_1", t("preset_dlg_tab_custom1")),
            ("custom_2", t("preset_dlg_tab_custom2")),
        ]
        self.seg_selector = MacSegmentedControl(items, self._active_key, self.card)
        self.seg_selector.segment_changed.connect(self._on_preset_switched)
        layout.addWidget(self.seg_selector)

        # 3. 参数编辑核心卡片 (MacInsetCard)
        self.card_edit = MacInsetCard(self.card)
        self.card_edit.set_theme(self._theme)

        # 3.1 预设名称编辑
        self.edit_name = QLineEdit(self.card_edit)
        self.edit_name.setPlaceholderText(t("preset_dlg_name_placeholder"))
        self.edit_name.setFixedHeight(28)
        self.edit_name.textChanged.connect(self._on_name_changed)

        self.row_name = MacSettingRow(t("preset_dlg_name_title"), t("preset_dlg_name_sub"), self.edit_name, parent=self.card_edit)
        self.card_edit.add_row(self.row_name)

        # 3.2 屏幕亮度微调滑块
        bright_widget = QWidget(self.card_edit)
        bright_layout = QHBoxLayout(bright_widget)
        bright_layout.setContentsMargins(0, 0, 0, 0)
        bright_layout.setSpacing(10)

        self.slider_bright = QSlider(Qt.Horizontal, bright_widget)
        self.slider_bright.setRange(1, 100)
        self.slider_bright.setFixedHeight(24)
        self.slider_bright.setCursor(Qt.PointingHandCursor)
        self.slider_bright.valueChanged.connect(self._on_bright_changed)

        self.lbl_bright_val = QLabel("90%", bright_widget)
        self.lbl_bright_val.setFixedWidth(44)
        self.lbl_bright_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_bright_val.setStyleSheet("font-size: 14px; font-weight: 700; color: #F5B338;")

        bright_layout.addWidget(self.slider_bright)
        bright_layout.addWidget(self.lbl_bright_val)

        self.row_bright = MacSettingRow(t("preset_dlg_bright_title"), t("preset_dlg_bright_sub"), bright_widget, parent=self.card_edit)
        self.card_edit.add_row(self.row_bright)

        # 3.3 护眼色温微调滑块
        warmth_widget = QWidget(self.card_edit)
        warmth_layout = QHBoxLayout(warmth_widget)
        warmth_layout.setContentsMargins(0, 0, 0, 0)
        warmth_layout.setSpacing(10)

        self.slider_warmth = QSlider(Qt.Horizontal, warmth_widget)
        self.slider_warmth.setRange(0, 100)
        self.slider_warmth.setFixedHeight(24)
        self.slider_warmth.setCursor(Qt.PointingHandCursor)
        self.slider_warmth.valueChanged.connect(self._on_warmth_changed)

        self.lbl_warmth_val = QLabel("0%", warmth_widget)
        self.lbl_warmth_val.setFixedWidth(44)
        self.lbl_warmth_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_warmth_val.setStyleSheet("font-size: 14px; font-weight: 700; color: #FCD34D;")

        warmth_layout.addWidget(self.slider_warmth)
        warmth_layout.addWidget(self.lbl_warmth_val)

        self.row_warmth = MacSettingRow(t("preset_dlg_warmth_title"), t("preset_dlg_warmth_sub"), warmth_widget, parent=self.card_edit)
        self.card_edit.add_row(self.row_warmth)

        # 3.4 深度压暗微芯片开关
        self.sw_boost = MacSwitch(parent=self.card_edit)
        self.sw_boost.set_theme(self._theme)
        self.sw_boost.toggled.connect(self._on_boost_toggled)

        self.row_boost = MacSettingRow(t("preset_dlg_boost_title"), t("preset_dlg_boost_sub"), self.sw_boost, is_last=True, parent=self.card_edit)
        self.card_edit.add_row(self.row_boost)

        layout.addWidget(self.card_edit)

        # 4. 辅助快捷工具栏
        helper_row = QHBoxLayout()
        helper_row.setSpacing(8)

        self.btn_capture = QPushButton(t("preset_dlg_capture"), self.card)
        self.btn_capture.setCursor(Qt.PointingHandCursor)
        self.btn_capture.setFixedHeight(26)
        self.btn_capture.setToolTip(t("preset_dlg_capture_tip"))
        self.btn_capture.clicked.connect(self._capture_current_screen)
        helper_row.addWidget(self.btn_capture)

        self.btn_preview = QPushButton(t("preset_dlg_preview"), self.card)
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setFixedHeight(26)
        self.btn_preview.setToolTip(t("preset_dlg_preview_tip"))
        self.btn_preview.clicked.connect(self._preview_current_values)
        helper_row.addWidget(self.btn_preview)

        helper_row.addStretch()

        self.btn_reset_def = QPushButton(t("preset_dlg_reset_default"), self.card)
        self.btn_reset_def.setCursor(Qt.PointingHandCursor)
        self.btn_reset_def.setFixedHeight(26)
        self.btn_reset_def.setToolTip(t("preset_dlg_reset_tip"))
        self.btn_reset_def.clicked.connect(self._reset_current_to_default)
        helper_row.addWidget(self.btn_reset_def)

        layout.addLayout(helper_row)

        layout.addStretch()

        # 5. 底部操作栏 (取消 + 保存并应用)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.lbl_tip = QLabel(t("preset_dlg_auto_sync_tip"), self.card)
        self.lbl_tip.setStyleSheet("font-size: 13px; color: #64748B; border: none; background: transparent;")
        bottom_row.addWidget(self.lbl_tip)

        bottom_row.addStretch()

        self.btn_cancel = QPushButton(t("preset_dlg_cancel"), self.card)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(30)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        bottom_row.addWidget(self.btn_cancel)

        self.btn_save = QPushButton(t("preset_dlg_save"), self.card)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedHeight(30)
        self.btn_save.clicked.connect(self._save_and_apply)
        bottom_row.addWidget(self.btn_save)

        layout.addLayout(bottom_row)

        self._apply_theme_styling()

    def _apply_theme_styling(self):
        """根据当前系统主题（深色 / 浅色 / 液态玻璃）注入统一微晶样式"""
        th = self._theme
        if th == "light":
            self.card.setStyleSheet("""
                QFrame#presetDialogCard {
                    background: rgba(255, 255, 255, 0.96);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 18px;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A; border: none; background: transparent;")
            self.lbl_tip.setStyleSheet("font-size: 13px; color: #64748B; border: none; background: transparent;")
            self.lbl_bright_val.setStyleSheet("font-size: 14px; font-weight: 700; color: #D97706; border: none; background: transparent;")
            self.lbl_warmth_val.setStyleSheet("font-size: 14px; font-weight: 700; color: #D97706; border: none; background: transparent;")

            self.edit_name.setStyleSheet("""
                QLineEdit {
                    background: rgba(0, 0, 0, 0.04);
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    border-radius: 6px;
                    padding: 3px 8px;
                    color: #1D1D1F;
                    font-size: 13px;
                    font-weight: 600;
                }
                QLineEdit:focus {
                    border-color: #007AFF;
                    background: #FFFFFF;
                }
            """)

            slider_css = """
                QSlider::groove:horizontal {
                    height: 5px;
                    background: rgba(0, 0, 0, 0.08);
                    border-radius: 2.5px;
                }
                QSlider::sub-page:horizontal {
                    background: #FF9500;
                    border-radius: 2.5px;
                }
                QSlider::handle:horizontal {
                    width: 16px;
                    height: 16px;
                    margin: -5.5px 0;
                    background: #FFFFFF;
                    border-radius: 8px;
                    border: 1px solid rgba(0, 0, 0, 0.20);
                }
            """
            self.slider_bright.setStyleSheet(slider_css)
            self.slider_warmth.setStyleSheet(slider_css)

            btn_subtle_css = """
                QPushButton {
                    background: rgba(0, 0, 0, 0.04);
                    border: 1px solid rgba(0, 0, 0, 0.10);
                    border-radius: 6px;
                    padding: 2px 10px;
                    color: #1D1D1F;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.08);
                    border-color: rgba(0, 0, 0, 0.20);
                }
            """
            self.btn_capture.setStyleSheet(btn_subtle_css)
            self.btn_preview.setStyleSheet(btn_subtle_css)
            self.btn_reset_def.setStyleSheet(btn_subtle_css)

            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #1D1D1F;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.09);
                    color: #1D1D1F;
                }
            """)

            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: #007AFF;
                    border: none;
                    border-radius: 8px;
                    padding: 4px 20px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0066D6;
                }
                QPushButton:pressed {
                    background: #0051AB;
                }
            """)
        elif th == "liquid_glass":
            self.card.setStyleSheet("""
                QFrame#presetDialogCard {
                    background: rgba(20, 22, 30, 0.94);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-top: 1.2px solid rgba(255, 255, 255, 0.38);
                    border-radius: 18px;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
            self.lbl_tip.setStyleSheet("font-size: 13px; color: rgba(235, 235, 245, 0.65); border: none; background: transparent;")

            self.edit_name.setStyleSheet("""
                QLineEdit {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-radius: 6px;
                    padding: 3px 8px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QLineEdit:focus {
                    border-color: #0A84FF;
                    background: rgba(255, 255, 255, 0.14);
                }
            """)

            slider_css = """
                QSlider::groove:horizontal {
                    height: 5px;
                    background: rgba(255, 255, 255, 0.15);
                    border-radius: 2.5px;
                }
                QSlider::sub-page:horizontal {
                    background: #FF9F0A;
                    border-radius: 2.5px;
                }
                QSlider::handle:horizontal {
                    width: 16px;
                    height: 16px;
                    margin: -5.5px 0;
                    background: #FFFFFF;
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.35);
                }
            """
            self.slider_bright.setStyleSheet(slider_css)
            self.slider_warmth.setStyleSheet(slider_css)

            btn_subtle_css = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-radius: 6px;
                    padding: 2px 10px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.16);
                    border-color: rgba(255, 255, 255, 0.35);
                }
            """
            self.btn_capture.setStyleSheet(btn_subtle_css)
            self.btn_preview.setStyleSheet(btn_subtle_css)
            self.btn_reset_def.setStyleSheet(btn_subtle_css)

            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.16);
                    color: #FFFFFF;
                }
            """)

            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: #0A84FF;
                    border: none;
                    border-radius: 8px;
                    padding: 4px 20px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0071E3;
                }
                QPushButton:pressed {
                    background: #005BB5;
                }
            """)
        else:
            # dark
            self.card.setStyleSheet("""
                QFrame#presetDialogCard {
                    background: #1C1C1E;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 18px;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
            self.lbl_tip.setStyleSheet("font-size: 13px; color: rgba(235, 235, 245, 0.60); border: none; background: transparent;")

            self.edit_name.setStyleSheet("""
                QLineEdit {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 6px;
                    padding: 3px 8px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QLineEdit:focus {
                    border-color: #0A84FF;
                    background: rgba(255, 255, 255, 0.08);
                }
            """)

            slider_css = """
                QSlider::groove:horizontal {
                    height: 5px;
                    background: rgba(255, 255, 255, 0.12);
                    border-radius: 2.5px;
                }
                QSlider::sub-page:horizontal {
                    background: #FF9F0A;
                    border-radius: 2.5px;
                }
                QSlider::handle:horizontal {
                    width: 16px;
                    height: 16px;
                    margin: -5.5px 0;
                    background: #FFFFFF;
                    border-radius: 8px;
                    border: 1px solid rgba(0, 0, 0, 0.25);
                }
            """
            self.slider_bright.setStyleSheet(slider_css)
            self.slider_warmth.setStyleSheet(slider_css)

            btn_subtle_css = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 6px;
                    padding: 2px 10px;
                    color: #F5F5F7;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.12);
                    border-color: rgba(255, 255, 255, 0.25);
                    color: #FFFFFF;
                }
            """
            self.btn_capture.setStyleSheet(btn_subtle_css)
            self.btn_preview.setStyleSheet(btn_subtle_css)
            self.btn_reset_def.setStyleSheet(btn_subtle_css)

            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 8px;
                    padding: 4px 16px;
                    color: #F5F5F7;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.14);
                    color: #FFFFFF;
                }
            """)

            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: #0A84FF;
                    border: none;
                    border-radius: 8px;
                    padding: 4px 20px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0071E3;
                }
                QPushButton:pressed {
                    background: #005BB5;
                }
            """)

        # 统一传播给卡片及其所有设置行、分段选择器与微动芯片
        if hasattr(self, "card_edit"):
            self.card_edit.set_theme(th)
        if hasattr(self, "seg_selector"):
            self.seg_selector.set_theme(th)
        if hasattr(self, "sw_boost"):
            self.sw_boost.set_theme(th)

    def apply_theme(self, theme: str):
        self._theme = theme if theme in ("dark", "light", "liquid_glass") else "dark"
        self._apply_theme_styling()

    def _load_preset_to_ui(self, key: str):
        """将选中的预设数据加载到编辑控件中"""
        data = self._presets_cache.get(key, DEFAULT_SCENE_PRESETS.get(key, {}))
        self.edit_name.blockSignals(True)
        self.slider_bright.blockSignals(True)
        self.slider_warmth.blockSignals(True)
        self.sw_boost.blockSignals(True)

        self.edit_name.setText(data.get("name", ""))
        b = int(data.get("brightness", 50))
        w = int(data.get("warmth", 0))
        boost = bool(data.get("boost_2x", False))

        self.slider_bright.setValue(b)
        self.lbl_bright_val.setText(f"{b}%")

        self.slider_warmth.setValue(w)
        self.lbl_warmth_val.setText(f"{w}%")

        self.sw_boost.setChecked(boost)

        self.edit_name.blockSignals(False)
        self.slider_bright.blockSignals(False)
        self.slider_warmth.blockSignals(False)
        self.sw_boost.blockSignals(False)

    def _on_preset_switched(self, key: str):
        """切换编辑的预设项"""
        self._active_key = key
        self._load_preset_to_ui(key)

    def _on_name_changed(self, text: str):
        if self._active_key in self._presets_cache:
            self._presets_cache[self._active_key]["name"] = text.strip()

    def _on_bright_changed(self, val: int):
        self.lbl_bright_val.setText(f"{val}%")
        if self._active_key in self._presets_cache:
            self._presets_cache[self._active_key]["brightness"] = val

    def _on_warmth_changed(self, val: int):
        self.lbl_warmth_val.setText(f"{val}%")
        if self._active_key in self._presets_cache:
            self._presets_cache[self._active_key]["warmth"] = val

    def _on_boost_toggled(self, checked: bool):
        if self._active_key in self._presets_cache:
            self._presets_cache[self._active_key]["boost_2x"] = checked

    def _capture_current_screen(self):
        """抓取此刻屏幕的真实亮度与色温"""
        b = self.engine.current_brightness
        w = self.engine.current_warmth
        boost = getattr(self.engine, "enhanced_2x", False)

        self.slider_bright.setValue(b)
        self.slider_warmth.setValue(w)
        self.sw_boost.setChecked(boost)

        if self._active_key in self._presets_cache:
            self._presets_cache[self._active_key]["brightness"] = b
            self._presets_cache[self._active_key]["warmth"] = w
            self._presets_cache[self._active_key]["boost_2x"] = boost

        self.lbl_tip.setText(t("preset_dlg_captured").format(b=b, w=w))

    def _preview_current_values(self):
        """临时将当前设定的参数应用到屏幕"""
        b = self.slider_bright.value()
        w = self.slider_warmth.value()
        boost = self.sw_boost.isChecked()

        if self.parent_window:
            self.parent_window.set_enhanced_2x(boost)
            self.parent_window.set_brightness(b)
            self.parent_window.set_warmth(w)
        else:
            self.engine.set_brightness(b)
            self.engine.set_warmth(w)

        self.lbl_tip.setText(t("preset_dlg_previewing"))

    def _reset_current_to_default(self):
        """恢复当前预设出厂值"""
        if self._active_key in DEFAULT_SCENE_PRESETS:
            self._presets_cache[self._active_key] = copy.deepcopy(DEFAULT_SCENE_PRESETS[self._active_key])
            self._load_preset_to_ui(self._active_key)
            self.lbl_tip.setText(t("preset_dlg_restored").format(name=self._presets_cache[self._active_key]["name"]))

    def _on_cancel_clicked(self):
        """取消时，如果刚才点过预览，还原屏幕初始参数"""
        if self.parent_window:
            self.parent_window.set_enhanced_2x(self._initial_screen_boost)
            self.parent_window.set_brightness(self._initial_screen_b)
            self.parent_window.set_warmth(self._initial_screen_w)
        self.reject()

    def _save_and_apply(self):
        """持久化保存所有已修改的预设，并即时生效应用当前选中的预设"""
        self.config.set_scene_presets(self._presets_cache)
        self.config.save()

        # 刷新主界面 6 大预设微晶药丸的文本与提示
        if self.parent_window and hasattr(self.parent_window, "_update_preset_pills"):
            self.parent_window._update_preset_pills()

        # 即时应用当前选中的预设
        if self.parent_window and hasattr(self.parent_window, "apply_scene"):
            self.parent_window.apply_scene(self._active_key)

        self.accept()
