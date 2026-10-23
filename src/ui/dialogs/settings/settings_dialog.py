"""Luna Dimmer - 苹果 macOS「系统设置」原生偏好设置中心主窗口 (SettingsDialog)

遵循 Apple Human Interface Guidelines (macOS Ventura / Sonoma / Sequoia):
1. 左上角红黄绿三色原生信号灯 (🔴 🟡 🟢)；
2. 左侧深空毛玻璃侧边栏 (195px)，配备四大超椭圆彩色图标徽标与磨砂胶囊；
3. 右侧 Inset Grouped 圆角卡片组与模块化分页容器 (QStackedWidget)；
4. 结构解耦：将各分页拆分为独立页面组件 (GeneralPage, OpticsPage, HotkeysPage, SafetyPage)；
5. 设计令牌中心化：通过 ThemeTokens 统一驱动三大视觉主题。
"""

from typing import Optional, List
import logging
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QCursor, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDialog,
    QStackedWidget,
    QGraphicsDropShadowEffect,
    QApplication,
)

from src.config import ConfigManager
from src.i18n import t, get_language, set_language
from src.updater import CURRENT_VERSION, UpdateWorker, UpgradeDialog, is_newer_version
from src.win32_compat import start_window_drag, set_windows_autostart
from src.widgets.mac_controls import (
    MacNavButton,
    MacTrafficLights,
)

from src.ui.dialogs.settings.general_page import GeneralPage
from src.ui.dialogs.settings.optics_page import OpticsPage
from src.ui.dialogs.settings.hotkeys_page import HotkeysPage, HotkeyEditButton, ACTION_KEY_MAP
from src.ui.dialogs.settings.safety_page import SafetyPage


class SettingsDialog(QDialog):
    """
    Apple macOS 原生风格「系统偏好设置」中心主对话框 (纯拟物架构)
    """
    sig_theme_changed = pyqtSignal(str)

    def __init__(self, config: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self.selected_theme = str(self.config.get("theme", "dark"))
        self.selected_lang = str(self.config.get("language", get_language()))
        set_language(self.selected_lang)

        self.setWindowTitle("Luna Dimmer - " + t("settings_title", "软件偏好设置"))
        self.setFixedSize(705, 590)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._drag_pos = QPoint()
        self._current_nav_index = 0
        self.worker = None
        self.nav_buttons: List[MacNavButton] = []
        self._init_ui()
        self.apply_theme(self.selected_theme)
        self.retranslate_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(0)

        # 外层超椭圆卡片容器
        self.card = QFrame(self)
        self.card.setObjectName("settingsCard")
        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 柔和弥散阴影
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(36)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(self.shadow)

        # ---------------------------------------------------------
        # 左侧侧边栏 (195px，经典 macOS Ventura 设计)
        # ---------------------------------------------------------
        self.sidebar = QFrame(self.card)
        self.sidebar.setObjectName("settingsSidebar")
        self.sidebar.setFixedWidth(195)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(8)

        # 1. 信号灯 (关闭与最小化)
        self.traffic_lights = MacTrafficLights(parent=self.sidebar)
        self.traffic_lights.sig_close.connect(self.close)
        self.traffic_lights.sig_min.connect(self.showMinimized)
        sidebar_layout.addWidget(self.traffic_lights)
        sidebar_layout.addSpacing(6)

        # 2. 侧边栏标题
        self.lbl_sidebar_title = QLabel(t("settings_title", "软件偏好设置"), self.sidebar)
        self.lbl_sidebar_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #FFFFFF; padding-left: 2px;")
        sidebar_layout.addWidget(self.lbl_sidebar_title)
        sidebar_layout.addSpacing(4)

        # 3. 导航项 (4大核心分组)
        nav_configs = [
            ("⚙️", ("#007AFF", "#0062D2"), t("tab_general"), 0),
            ("👁️", ("#FF9500", "#D97706"), t("tab_optics"), 1),
            ("⌨️", ("#5E5CE6", "#4B4AC4"), t("tab_hotkeys"), 2),
            ("🛡️", ("#34C759", "#28A745"), t("tab_system"), 3),
        ]
        for icon, grad, title, idx in nav_configs:
            btn = MacNavButton(icon, grad, title, self.sidebar)
            btn.clicked.connect(lambda *args, i=idx: self._on_nav_clicked(i))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        card_layout.addWidget(self.sidebar)

        # ---------------------------------------------------------
        # 右侧内容展示区 (QStackedWidget)
        # ---------------------------------------------------------
        self.content_pane = QFrame(self.card)
        self.content_pane.setObjectName("settingsContent")
        content_layout = QVBoxLayout(self.content_pane)
        content_layout.setContentsMargins(20, 14, 20, 12)
        content_layout.setSpacing(10)

        # 顶栏：当前分组标题 + 场景预设快捷入口
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        self.lbl_tab_header = QLabel(t("tab_general"), self.content_pane)
        self.lbl_tab_header.setStyleSheet("font-size: 17px; font-weight: 700; color: #FFFFFF;")
        top_bar.addWidget(self.lbl_tab_header)
        top_bar.addStretch()
        content_layout.addLayout(top_bar)

        # Stacked Pages
        self.stack = QStackedWidget(self.content_pane)
        self.general_page = GeneralPage(self)
        self.optics_page = OpticsPage(self)
        self.hotkeys_page = HotkeysPage(self)
        self.safety_page = SafetyPage(self)

        self.stack.addWidget(self.general_page)
        self.stack.addWidget(self.optics_page)
        self.stack.addWidget(self.hotkeys_page)
        self.stack.addWidget(self.safety_page)
        content_layout.addWidget(self.stack, 1)

        # 底部操作栏
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(2, 0, 2, 0)

        self.lbl_auto_save_tip = QLabel("✓ " + t("auto_save_tip", "偏好设置即时生效并自动保存"), self.content_pane)
        self.lbl_auto_save_tip.setStyleSheet("font-size: 12px; font-weight: 500; color: #64748B;")
        footer_layout.addWidget(self.lbl_auto_save_tip)
        footer_layout.addStretch()

        self.btn_save = QPushButton(t("btn_save"), self.content_pane)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedHeight(30)
        self.btn_save.clicked.connect(self.save_and_close)
        footer_layout.addWidget(self.btn_save)

        content_layout.addLayout(footer_layout)
        card_layout.addWidget(self.content_pane, 1)
        root_layout.addWidget(self.card)

        # 默认选中第 0 页
        self._on_nav_clicked(0)
        self.setFixedSize(705, 590)

    def sizeHint(self) -> QSize:
        return QSize(705, 590)

    def minimumSizeHint(self) -> QSize:
        return QSize(705, 590)

    # -------------------------------------------------------------
    # 向后兼容属性映射 (Backward Compatibility Proxies)
    # -------------------------------------------------------------
    @property
    def startup_switch(self):
        return self.general_page.startup_switch

    @property
    def remember_pos_switch(self):
        return self.general_page.remember_pos_switch

    @property
    def autoupdate_switch(self):
        return self.general_page.autoupdate_switch

    @property
    def seg_theme(self):
        return self.general_page.seg_theme

    @property
    def seg_lang(self):
        return self.general_page.seg_lang

    @property
    def theme_segment(self):
        return self.general_page.seg_theme

    @property
    def lang_segment(self):
        return self.general_page.seg_lang

    @property
    def stealth_bezier_switch(self):
        return self.optics_page.stealth_bezier_switch

    @property
    def hotkey_buttons(self):
        return self.hotkeys_page.hotkey_buttons

    @property
    def btn_reset_hotkeys(self):
        return self.hotkeys_page.btn_reset_hotkeys

    @property
    def btn_reset(self):
        return self.safety_page.btn_reset

    @property
    def btn_open_sponsor(self):
        return self.safety_page.btn_open_sponsor

    @property
    def btn_open_feedback(self):
        return self.safety_page.btn_open_feedback

    # -------------------------------------------------------------
    # 导航与交互逻辑
    # -------------------------------------------------------------
    def stop_all_hotkey_recordings(self, exclude=None):
        """代理停止所有快捷键录制态"""
        if hasattr(self, "hotkeys_page") and hasattr(self.hotkeys_page, "stop_all_hotkey_recordings"):
            self.hotkeys_page.stop_all_hotkey_recordings(exclude=exclude)

    def check_internal_conflict(self, current_action_key: str, candidate_key: str):
        """代理调用 HotkeysPage 内部按键冲突检测"""
        if hasattr(self, "hotkeys_page") and hasattr(self.hotkeys_page, "check_internal_conflict"):
            return self.hotkeys_page.check_internal_conflict(current_action_key, candidate_key)
        return None

    def show_hotkey_status(self, msg: str, is_error: bool = False):
        """代理显示快捷键即时录制反馈状态"""
        if hasattr(self, "hotkeys_page") and hasattr(self.hotkeys_page, "show_hotkey_status"):
            self.hotkeys_page.show_hotkey_status(msg, is_error)

    def save_and_close(self):
        """保存并平滑关闭对话框（兼容旧版调用契约）"""
        try:
            self.config.save()
            parent = self.parent()
            if parent and hasattr(parent, "reload_hotkeys"):
                parent.reload_hotkeys()
        except Exception:
            pass
        self.accept()

    def _on_nav_clicked(self, index: int):
        self._current_nav_index = index
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.set_selected(i == index)
        tab_names = [t("tab_general"), t("tab_optics"), t("tab_hotkeys"), t("tab_system")]
        if 0 <= index < len(tab_names):
            self.lbl_tab_header.setText(tab_names[index])
            logging.info(f"[SettingsDialog] 切换至选项卡 [{index}]: {tab_names[index]}")

    def _select_theme(self, theme_val: str):
        """选择外观主题（深色 / 浅色 / 液态玻璃）并即时 0 延迟联动生效"""
        if theme_val != self.selected_theme:
            self.selected_theme = theme_val
            if hasattr(self.general_page, "seg_theme"):
                self.general_page.seg_theme.set_active_id(theme_val)
            self.apply_theme(theme_val)
            QApplication.processEvents()
            self.sig_theme_changed.emit(theme_val)
            self.config.set("theme", theme_val)
            self.config.save()

    def _select_language(self, lang: str):
        """选择界面语言并即时全量重绘"""
        self.selected_lang = lang
        if hasattr(self.general_page, "seg_lang"):
            self.general_page.seg_lang.set_active_id(lang)
        set_language(lang)
        self.config.set("language", lang)
        self.config.save()
        self.retranslate_ui()
        parent = self.parent()
        if parent and hasattr(parent, "retranslate_ui"):
            parent.retranslate_ui(lang)

    def sync_from_config(self):
        """从主配置热同步最新状态（避免多次修改漂移）"""
        self.setEnabled(True)
        curr_lang = str(self.config.get("language", "zh-CN"))
        if curr_lang != self.selected_lang:
            self.selected_lang = curr_lang
            set_language(curr_lang)
            if hasattr(self.general_page, "seg_lang"):
                self.general_page.seg_lang.set_active_id(curr_lang)
            self.retranslate_ui()

        curr_theme = str(self.config.get("theme", "dark"))
        if curr_theme != self.selected_theme:
            self.selected_theme = curr_theme
            if hasattr(self.general_page, "seg_theme"):
                self.general_page.seg_theme.set_active_id(curr_theme)
            self.apply_theme(curr_theme)

        # 同步过程必须屏蔽信号：否则 setChecked 会反向触发 toggled 槽，
        # 把「读配置」变成「写配置」，甚至每次打开设置都重写一次注册表自启项。
        switches = [
            (self.general_page.startup_switch, bool(self.config.get("autostart", False))),
            (self.general_page.remember_pos_switch, bool(self.config.get("remember_window_position", True))),
            (self.general_page.autoupdate_switch, bool(self.config.get("auto_update", True))),
            (self.optics_page.stealth_bezier_switch, bool(self.config.get("smooth_wake", True))),
        ]
        if hasattr(self.general_page, "fullscreen_guard_switch"):
            switches.append(
                (self.general_page.fullscreen_guard_switch, bool(self.config.get("fullscreen_guard", True)))
            )

        for switch, value in switches:
            switch.blockSignals(True)
            switch.setChecked(value)
            switch.blockSignals(False)

        self.safety_page.apply_theme(self.selected_theme)

    def _open_preset_customizer(self):
        from src.widgets.preset_dialog import PresetCustomizerDialog
        parent_main = self.parent()
        engine = getattr(parent_main, "engine", None)
        active_key = getattr(parent_main, "current_scene_key", "work") or "work"
        dlg = PresetCustomizerDialog(
            config=self.config,
            engine=engine,
            parent=parent_main,
            initial_preset_key=active_key,
        )
        dlg.exec_()

    def _check_updates_online(self):
        """检查版本更新流程（单个在飞 worker，杜绝重复点击产生野线程）"""
        if self.worker is not None and self.worker.isRunning():
            return

        row_update = getattr(self.general_page, "row_update", None)
        btn_check = getattr(self.general_page, "btn_check_update", None)
        lbl_target = getattr(row_update, "lbl_title", None)
        if lbl_target:
            lbl_target.setText(t("connecting_server", "正在连接服务器检查更新..."))
        if btn_check:
            btn_check.setEnabled(False)
            btn_check.setText(t("checking_update", "正在检查..."))

        self.worker = UpdateWorker(parent=self)

        def on_worker_finished(success: bool, data: dict, error_msg: str):
            worker = self.worker
            if worker is not None:
                worker.deleteLater()
                self.worker = None

            if btn_check:
                btn_check.setEnabled(True)
                btn_check.setText(t("btn_check_update", "检查更新"))

            if success and data:
                remote_ver = data.get("version", "")
                if is_newer_version(remote_ver, CURRENT_VERSION):
                    if hasattr(self.parent(), "_cached_update_data"):
                        self.parent()._cached_update_data = data

                    # 首页面不提示不显示，仅在偏好设置侧边栏「常规与启动」及更新条目展示精致红点
                    if hasattr(self, "nav_buttons") and len(self.nav_buttons) > 0:
                        self.nav_buttons[0].set_badge(True)

                    if lbl_target:
                        lbl_target.setText(f"🔴 {t('current_version', '当前版本')}: V{CURRENT_VERSION} ➔ V{remote_ver}")
                    if btn_check:
                        btn_check.setText(f"🔴 {t('btn_view_update', '查看更新')}")
                    dlg = UpgradeDialog(update_info=data, parent=self)
                    result = dlg.exec_()
                    if result == QDialog.Accepted:
                        if hasattr(self, "nav_buttons") and len(self.nav_buttons) > 0:
                            self.nav_buttons[0].set_badge(False)
                    else:
                        if hasattr(self.parent(), "_dismissed_update_version"):
                            self.parent()._dismissed_update_version = remote_ver
                else:
                    if lbl_target:
                        lbl_target.setText(f"✓ {t('latest_version', '当前已是最新版本')}")
                        QTimer.singleShot(3500, lambda: lbl_target.setText(f"{t('current_version', '当前版本')}: V{CURRENT_VERSION}") if lbl_target else None)
            else:
                if lbl_target:
                    lbl_target.setText(f"✕ {t('check_failed', '检查更新失败，请稍后重试')}")
                    QTimer.singleShot(3500, lambda: lbl_target.setText(f"{t('current_version', '当前版本')}: V{CURRENT_VERSION}") if lbl_target else None)

        # 显式队列连接：on_worker_finished 会操作控件，必须确定性地回到 GUI 线程执行
        self.worker.sig_finished.connect(on_worker_finished, Qt.QueuedConnection)
        self.worker.start()

    def prompt_restore_defaults(self):
        """唤出高危出厂重置确认拦截"""
        self.safety_page.prompt_restore_defaults()

    def restore_defaults(self):
        """兼容入口"""
        self.prompt_restore_defaults()

    def _do_restore_defaults(self):
        """执行彻底出厂重置：配置、注册表、运行中的热键 / 预设面板 / 主题全部即时生效"""
        self.config.reset_to_defaults()
        try:
            set_windows_autostart("LunaDimmer", False)
        except Exception:
            pass

        # 1. 开关 UI 同步（屏蔽信号，避免把「读默认值」又写回配置文件）
        switches = [
            (self.general_page.startup_switch, False),
            (self.general_page.remember_pos_switch, True),
            (self.optics_page.stealth_bezier_switch, True),
            (self.general_page.autoupdate_switch, True),
        ]
        if hasattr(self.general_page, "fullscreen_guard_switch"):
            switches.append((self.general_page.fullscreen_guard_switch, True))
        for switch, value in switches:
            switch.blockSignals(True)
            switch.setChecked(value)
            switch.blockSignals(False)

        # 2. 快捷键：重置 UI + 持久化 + 运行时监听热重载（一步到位）
        self.hotkeys_page.reset_only_hotkeys()

        # 3. 主题与语言（内部会自动广播给主窗口）
        self._select_theme("dark")
        self._select_language("zh-CN")

        # 4. 主界面 6 大预设药丸文本刷新（真实方法名是 _update_preset_pills）
        parent = self.parent()
        if parent and hasattr(parent, "_update_preset_pills"):
            try:
                parent._update_preset_pills()
            except Exception:
                pass

        if hasattr(self, "lbl_auto_save_tip"):
            self.lbl_auto_save_tip.setText(t("reset_done_toast", "✓ 已成功恢复所有出厂默认设置"))
            self.lbl_auto_save_tip.setStyleSheet("font-size: 12px; font-weight: 600; color: #34D399; background: transparent;")
            QTimer.singleShot(3500, lambda: self.lbl_auto_save_tip.setText("✓ " + t("auto_save_tip")) if getattr(self, "lbl_auto_save_tip", None) else None)

    # -------------------------------------------------------------
    # 集中主题切换驱动 (Theme Engine Delegation)
    # -------------------------------------------------------------
    def apply_theme(self, theme: str):
        self.selected_theme = theme if theme in ("dark", "light", "liquid_glass") else "dark"
        cur_th = self.selected_theme

        # 1. 窗口壳体与侧边栏样式
        if cur_th == "light":
            self.card.setStyleSheet("""
                QFrame#settingsCard {
                    background: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.10);
                    border-radius: 14px;
                }
            """)
            self.sidebar.setStyleSheet("""
                QFrame#settingsSidebar {
                    background: rgba(238, 238, 242, 0.95);
                    border-top-left-radius: 14px;
                    border-bottom-left-radius: 14px;
                    border-right: 1px solid rgba(0, 0, 0, 0.08);
                }
            """)
            self.lbl_sidebar_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #1D1D1F; padding-left: 2px;")
            self.lbl_tab_header.setStyleSheet("font-size: 17px; font-weight: 700; color: #1D1D1F;")
            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: #007AFF;
                    border: none;
                    border-radius: 8px;
                    padding: 4px 22px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0066D6;
                }
                QPushButton:pressed {
                    background: #0051AB;
                }
            """)
            self.lbl_auto_save_tip.setStyleSheet("font-size: 12px; font-weight: 500; color: rgba(60, 60, 67, 0.65);")
        elif cur_th == "liquid_glass":
            self.card.setStyleSheet("""
                QFrame#settingsCard {
                    background: rgba(20, 22, 30, 0.92);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-top: 1.2px solid rgba(255, 255, 255, 0.38);
                    border-radius: 14px;
                }
            """)
            self.sidebar.setStyleSheet("""
                QFrame#settingsSidebar {
                    background: rgba(14, 16, 22, 0.70);
                    border-top-left-radius: 14px;
                    border-bottom-left-radius: 14px;
                    border-right: 1px solid rgba(255, 255, 255, 0.10);
                }
            """)
            self.lbl_sidebar_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #FFFFFF; padding-left: 2px;")
            self.lbl_tab_header.setStyleSheet("font-size: 17px; font-weight: 700; color: #FFFFFF;")
            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: #0A84FF;
                    border: none;
                    border-radius: 8px;
                    padding: 4px 22px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0071E3;
                }
                QPushButton:pressed {
                    background: #005BB5;
                }
            """)
            self.lbl_auto_save_tip.setStyleSheet("font-size: 12px; font-weight: 500; color: rgba(235, 235, 245, 0.65);")
        else:  # Dark
            self.card.setStyleSheet("""
                QFrame#settingsCard {
                    background: #1C1C1E;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 14px;
                }
            """)
            self.sidebar.setStyleSheet("""
                QFrame#settingsSidebar {
                    background: rgba(28, 28, 30, 0.90);
                    border-top-left-radius: 14px;
                    border-bottom-left-radius: 14px;
                    border-right: 1px solid rgba(255, 255, 255, 0.08);
                }
            """)
            self.lbl_sidebar_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #FFFFFF; padding-left: 2px;")
            self.lbl_tab_header.setStyleSheet("font-size: 17px; font-weight: 700; color: #FFFFFF;")
            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: #0A84FF;
                    border: none;
                    border-radius: 8px;
                    padding: 4px 22px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0071E3;
                }
                QPushButton:pressed {
                    background: #005BB5;
                }
            """)
            self.lbl_auto_save_tip.setStyleSheet("font-size: 12px; font-weight: 500; color: rgba(235, 235, 245, 0.60);")

        # 2. 侧边栏按钮样式
        for btn in self.nav_buttons:
            btn.apply_theme(cur_th)

        # 3. 分发给各页面自主更新主题
        self.general_page.apply_theme(cur_th)
        self.optics_page.apply_theme(cur_th)
        self.hotkeys_page.apply_theme(cur_th)
        self.safety_page.apply_theme(cur_th)

    def retranslate_ui(self):
        """全量多语言刷新"""
        self.lbl_sidebar_title.setText(t("settings_title", "软件偏好设置"))
        tab_titles = [
            t("tab_general", "常规与启动"),
            t("tab_optics", "调光与护眼"),
            t("tab_hotkeys", "全局快捷键"),
            t("tab_system", "安全守护与重置"),
        ]
        for idx, btn in enumerate(self.nav_buttons):
            if idx < len(tab_titles):
                btn.set_text(tab_titles[idx])

        cur_idx = self.stack.currentIndex()
        if 0 <= cur_idx < len(tab_titles):
            self.lbl_tab_header.setText(tab_titles[cur_idx])

        self.btn_save.setText(t("btn_save"))
        self.lbl_auto_save_tip.setText("✓ " + t("auto_save_tip"))

        # 分发给各页面自主重绘文案
        self.general_page.retranslate()
        self.optics_page.retranslate()
        self.hotkeys_page.retranslate()
        self.safety_page.retranslate()

    def showEvent(self, event):
        super().showEvent(event)
        # 1. 防御性自愈：强制释放任何系统级与 Qt 内部可能遗留的鼠标捕获
        try:
            import ctypes
            ctypes.windll.user32.ReleaseCapture()
            grabber = QApplication.mouseGrabber()
            if grabber:
                grabber.releaseMouse()
        except Exception:
            pass

        # 2. 每次打开确保外壳、侧边栏、内容区及所有子页面处于 Enabled 可交互状态
        self.setEnabled(True)
        if hasattr(self, "card") and self.card:
            self.card.setEnabled(True)
        if hasattr(self, "sidebar") and self.sidebar:
            self.sidebar.setEnabled(True)
        if hasattr(self, "content_pane") and self.content_pane:
            self.content_pane.setEnabled(True)
        if hasattr(self, "stack") and self.stack:
            self.stack.setEnabled(True)

        for page in (
            getattr(self, "general_page", None),
            getattr(self, "optics_page", None),
            getattr(self, "hotkeys_page", None),
            getattr(self, "safety_page", None),
        ):
            if page:
                page.setEnabled(True)
        # 恢复上次停留的分组（打开设置不应每次都把用户甩回第一页）
        self._on_nav_clicked(self._current_nav_index)

        # 静默感知：若已探测到新版本，首页面不提示，仅在偏好设置侧边栏及条目呈现红点就绪态
        parent_cached = getattr(self.parent(), "_cached_update_data", None)
        if parent_cached and isinstance(parent_cached, dict):
            cached_ver = parent_cached.get("version", "")
            if is_newer_version(cached_ver, CURRENT_VERSION):
                if hasattr(self, "nav_buttons") and len(self.nav_buttons) > 0:
                    self.nav_buttons[0].set_badge(True)

                row_update = getattr(self.general_page, "row_update", None)
                lbl_target = getattr(row_update, "lbl_title", None)
                btn_check = getattr(self.general_page, "btn_check_update", None)
                if lbl_target:
                    lbl_target.setText(f"🔴 {t('current_version', '当前版本')}: V{CURRENT_VERSION} ➔ V{cached_ver}")
                if btn_check:
                    btn_check.setText(f"🔴 {t('btn_view_update', '查看更新')}")

        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # 严格限制：仅在右侧内容区的顶部空白条 (X > 210, Y <= 44) 响应拖拽，绝对不侵占左侧侧边栏任何区域
            if event.pos().x() > 210 and event.pos().y() <= 44:
                start_window_drag(int(self.winId()))
                event.accept()
                return
        super().mousePressEvent(event)
