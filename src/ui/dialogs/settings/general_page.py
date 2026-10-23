"""Luna Dimmer - 设置中心：常规与启动分页 (General Page)

包含：
1. ☀️/🌙/💧 三大拟物视觉主题选择分段器；
2. 🚀 开机自启动、窗口记忆位置；
3. 🌐 界面中英多语言切换；
4. 🔄 在线版本检测与一键更新入口。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)

from src.i18n import t
from src.updater import CURRENT_VERSION, UpdateWorker, UpgradeDialog, is_newer_version
from src.win32_compat import set_windows_autostart
from src.widgets.mac_controls import (
    MacSwitch,
    MacSegmentedControl,
    MacInsetCard,
    MacSettingRow,
)


class GeneralPage(QWidget):
    """常规与启动偏好设置页面"""

    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog
        self.config = parent_dialog.config
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. 外观主题分段胶囊卡片 (🌙 深色 / ☀️ 浅色 / 💧 液态玻璃)
        self.card_theme = MacInsetCard(self)
        self.seg_theme = MacSegmentedControl(
            [("dark", t("theme_dark")), ("light", t("theme_light")), ("liquid_glass", t("theme_liquid_glass"))],
            self.parent_dialog.selected_theme,
            self.card_theme,
        )
        self.seg_theme.segment_changed.connect(self._on_theme_changed)
        self.row_theme = MacSettingRow(t("theme_title"), "", self.seg_theme, is_last=True, parent=self.card_theme)
        self.card_theme.add_row(self.row_theme)
        layout.addWidget(self.card_theme)

        # 2. 系统集成与启动行为卡片 (Inset Grouped)
        self.card_gen = MacInsetCard(self)

        # 2.1 开机自启
        self.startup_switch = MacSwitch(self.card_gen)
        self.startup_switch.setChecked(bool(self.config.get("autostart", False)))
        self.startup_switch.toggled.connect(self._on_startup_toggled)
        self.row_startup = MacSettingRow(
            t("pref_startup"),
            t("pref_startup_sub"),
            self.startup_switch,
            is_last=False,
            parent=self.card_gen,
        )
        self.card_gen.add_row(self.row_startup)

        # 2.2 记忆窗口位置
        self.remember_pos_switch = MacSwitch(self.card_gen)
        self.remember_pos_switch.setChecked(bool(self.config.get("remember_window_position", True)))
        self.remember_pos_switch.toggled.connect(
            lambda val: (self.config.set("remember_window_position", val), self.config.save())
        )
        self.row_remember = MacSettingRow(
            t("pref_remember"),
            t("pref_remember_sub"),
            self.remember_pos_switch,
            is_last=False,
            parent=self.card_gen,
        )
        self.card_gen.add_row(self.row_remember)

        # 2.3 全屏游戏与演示防抢焦点
        self.fullscreen_guard_switch = MacSwitch(self.card_gen)
        self.fullscreen_guard_switch.setChecked(bool(self.config.get("fullscreen_guard", True)))
        self.fullscreen_guard_switch.toggled.connect(
            lambda val: (self.config.set("fullscreen_guard", val), self.config.save())
        )
        self.row_fullscreen_guard = MacSettingRow(
            t("sys_fullscreen_guard", "全屏游戏与演示时禁止快捷键弹窗抢焦点"),
            t("sys_fullscreen_guard_sub", "处于全屏独占应用时快捷键仅在后台平滑调光，不打断游戏与视频"),
            self.fullscreen_guard_switch,
            is_last=False,
            parent=self.card_gen,
        )
        self.card_gen.add_row(self.row_fullscreen_guard)

        # 2.4 语言选择
        self.seg_lang = MacSegmentedControl(
            [("zh-CN", "简体中文"), ("en-US", "English")],
            self.parent_dialog.selected_lang,
            self.card_gen,
        )
        self.seg_lang.segment_changed.connect(self._on_lang_changed)
        self.row_lang = MacSettingRow(t("pref_lang"), "", self.seg_lang, is_last=True, parent=self.card_gen)
        self.card_gen.add_row(self.row_lang)
        layout.addWidget(self.card_gen)

        # 3. 软件维护与在线版本更新卡片
        self.card_update = MacInsetCard(self)

        # 3.1 自动检查更新微动开关
        self.autoupdate_switch = MacSwitch(self.card_update)
        self.autoupdate_switch.setChecked(bool(self.config.get("auto_update", True)))
        self.autoupdate_switch.toggled.connect(
            lambda val: (self.config.set("auto_update", val), self.config.save())
        )
        self.row_autoupdate = MacSettingRow(
            t("auto_update"),
            t("auto_update_sub"),
            self.autoupdate_switch,
            is_last=False,
            parent=self.card_update,
        )
        self.card_update.add_row(self.row_autoupdate)

        # 3.2 在线检测更新操作按钮
        self.btn_check_update = QPushButton(t("btn_check_update"), self.card_update)
        self.btn_check_update.setCursor(Qt.PointingHandCursor)
        self.btn_check_update.setFixedHeight(28)
        self.btn_check_update.clicked.connect(self._on_check_update_clicked)

        self.row_update = MacSettingRow(
            f"{t('current_version', '当前版本')}: v{CURRENT_VERSION}",
            "",
            self.btn_check_update,
            is_last=False,
            parent=self.card_update,
        )
        self.card_update.add_row(self.row_update)

        # 3.3 官方网站
        self.btn_visit_site = QPushButton(t("btn_visit_website", "🌐 访问官网"), self.card_update)
        self.btn_visit_site.setCursor(Qt.PointingHandCursor)
        self.btn_visit_site.setFixedHeight(28)
        self.btn_visit_site.clicked.connect(self._on_visit_site_clicked)

        self.row_website = MacSettingRow(
            t("official_website", "官方网站"),
            "https://lunadimmer.pages.dev/",
            self.btn_visit_site,
            is_last=False,
            parent=self.card_update,
        )
        self.card_update.add_row(self.row_website)

        # 3.4 开发者 QQ
        self.btn_copy_qq = QPushButton(t("btn_copy_qq", "📋 复制"), self.card_update)
        self.btn_copy_qq.setCursor(Qt.PointingHandCursor)
        self.btn_copy_qq.setFixedHeight(28)
        self.btn_copy_qq.clicked.connect(self._on_copy_qq_clicked)

        self.row_qq = MacSettingRow(
            t("contact_qq", "联系作者 / QQ"),
            "1115406747@qq.com",
            self.btn_copy_qq,
            is_last=True,
            parent=self.card_update,
        )
        self.card_update.add_row(self.row_qq)
        layout.addWidget(self.card_update)

        layout.addStretch()

    def _on_theme_changed(self, val):
        if isinstance(val, int):
            themes = ["dark", "light", "liquid_glass"]
            theme_val = themes[val] if 0 <= val < len(themes) else "dark"
        else:
            theme_val = str(val)
        if theme_val in ("dark", "light", "liquid_glass"):
            self.parent_dialog._select_theme(theme_val)

    def _on_lang_changed(self, val):
        if isinstance(val, int):
            langs = ["zh-CN", "en-US"]
            lang_val = langs[val] if 0 <= val < len(langs) else "zh-CN"
        else:
            lang_val = str(val)
        if lang_val in ("zh-CN", "en-US"):
            self.parent_dialog._select_language(lang_val)

    def _on_startup_toggled(self, checked: bool):
        """把自启开关写入注册表；写失败时立即回退 UI，绝不制造「看起来开了其实没开」的假象"""
        try:
            ok = bool(set_windows_autostart("LunaDimmer", checked))
        except Exception:
            ok = False

        if not ok:
            self.startup_switch.blockSignals(True)
            self.startup_switch.setChecked(not checked)
            self.startup_switch.blockSignals(False)
            self.config.set("autostart", not checked)
            self.config.set("autostart_write_failed", True)
            self.config.save()
            return

        self.config.set("autostart", checked)
        self.config.set("autostart_write_failed", False)
        self.config.save()

    def _on_check_update_clicked(self):
        self.parent_dialog._check_updates_online()

    def _on_visit_site_clicked(self):
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl, QTimer
        import webbrowser
        self.btn_visit_site.clearFocus()
        # 延时 50ms 异步唤起浏览器，确保 QPushButton 的 mouseReleaseEvent 与绘制完全出栈，杜绝焦点被外部进程抢夺导致交互卡死
        def do_open():
            try:
                webbrowser.open("https://lunadimmer.pages.dev/")
            except Exception:
                QDesktopServices.openUrl(QUrl("https://lunadimmer.pages.dev/"))
        QTimer.singleShot(50, do_open)

    def _on_copy_qq_clicked(self):
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        self.btn_copy_qq.clearFocus()
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText("1115406747@qq.com")
        self.btn_copy_qq.setText(t("copied", "✓ 已复制"))
        QTimer.singleShot(2000, lambda: self.btn_copy_qq.setText(t("btn_copy_qq", "📋 复制")) if hasattr(self, "btn_copy_qq") and self.btn_copy_qq else None)

    def set_update_available(self, available: bool, remote_ver: str = ""):
        """方案二：左侧纯净保持当前版本，右侧按钮视觉跃升为高对比度品牌蓝行动按钮【立即更新】"""
        self._update_available = bool(available)
        self._remote_ver = remote_ver
        if hasattr(self, "row_update") and hasattr(self.row_update, "lbl_title"):
            # 严格遵循用户指令：不显示 v1.0.0 → v1.0.1，始终纯净展示当前版本
            self.row_update.lbl_title.setText(f"{t('current_version', '当前版本')}: v{CURRENT_VERSION}")

        if hasattr(self, "btn_check_update"):
            if self._update_available:
                self.btn_check_update.setText(t("btn_update_now", "立即更新"))
                self.btn_check_update.setToolTip(f"新版本 v{remote_ver} 已就绪，点击升级" if remote_ver else "")
                self.btn_check_update.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0A84FF, stop:1 #0071E3);
                        border: 1px solid rgba(255, 255, 255, 0.30);
                        border-radius: 6px;
                        color: #FFFFFF;
                        font-size: 12.5px;
                        font-weight: 700;
                        padding: 2px 14px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2997FF, stop:1 #0A84FF);
                        border-color: rgba(255, 255, 255, 0.50);
                        color: #FFFFFF;
                    }
                    QPushButton:pressed {
                        background: #005BB5;
                    }
                """)
            else:
                self.btn_check_update.setText(t("btn_check_update", "检查更新"))
                self.btn_check_update.setToolTip("")
                btn_style = getattr(self, "_cached_btn_style", "")
                if btn_style:
                    self.btn_check_update.setStyleSheet(btn_style)

    def apply_theme(self, theme: str):
        for card in [self.card_theme, self.card_gen, self.card_update]:
            card.apply_theme(theme)
        for seg in [self.seg_theme, self.seg_lang]:
            seg.apply_theme(theme)
        for sw in [self.startup_switch, self.remember_pos_switch, self.autoupdate_switch]:
            sw.update()

        # 更新检查与官网跳转按钮样式适配 (Apple Secondary Control Capsule)
        btn_style = ""
        if theme == "light":
            btn_style = """
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 6px;
                    color: #1D1D1F;
                    font-size: 12.5px;
                    font-weight: 600;
                    padding: 2px 14px;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.09);
                    border-color: rgba(0, 0, 0, 0.20);
                }
                QPushButton:pressed {
                    background: rgba(0, 0, 0, 0.14);
                }
            """
        elif theme == "liquid_glass":
            btn_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.10);
                    border: 1px solid rgba(255, 255, 255, 0.20);
                    border-radius: 6px;
                    color: #FFFFFF;
                    font-size: 12.5px;
                    font-weight: 600;
                    padding: 2px 14px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.18);
                    border-color: rgba(255, 255, 255, 0.35);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.25);
                }
            """
        else:
            btn_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 6px;
                    color: #F5F5F7;
                    font-size: 12.5px;
                    font-weight: 600;
                    padding: 2px 14px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                    border-color: rgba(255, 255, 255, 0.25);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.22);
                }
            """
        self._cached_btn_style = btn_style
        if getattr(self, "_update_available", False):
            self.set_update_available(True, getattr(self, "_remote_ver", ""))
        else:
            self.btn_check_update.setStyleSheet(btn_style)
        if hasattr(self, "btn_visit_site"):
            self.btn_visit_site.setStyleSheet(btn_style)
        if hasattr(self, "btn_copy_qq"):
            self.btn_copy_qq.setStyleSheet(btn_style)

    def retranslate(self):
        self.row_theme.lbl_title.setText(t("theme_title"))
        self.seg_theme.update_item_labels([
            ("dark", t("theme_dark")),
            ("light", t("theme_light")),
            ("liquid_glass", t("theme_liquid_glass")),
        ])
        self.row_startup.lbl_title.setText(t("pref_startup"))
        self.row_startup.lbl_sub.setText(t("pref_startup_sub"))
        self.row_remember.lbl_title.setText(t("pref_remember"))
        self.row_remember.lbl_sub.setText(t("pref_remember_sub"))
        if hasattr(self, "row_fullscreen_guard"):
            self.row_fullscreen_guard.lbl_title.setText(t("sys_fullscreen_guard", "全屏游戏与演示时禁止快捷键弹窗抢焦点"))
            self.row_fullscreen_guard.lbl_sub.setText(t("sys_fullscreen_guard_sub", "处于全屏独占应用时快捷键仅在后台平滑调光，不打断游戏与视频"))
        self.row_lang.lbl_title.setText(t("pref_lang"))
        self.row_autoupdate.lbl_title.setText(t("auto_update"))
        self.row_autoupdate.lbl_sub.setText(t("auto_update_sub"))
        self.row_update.lbl_title.setText(f"{t('current_version', '当前版本')}: v{CURRENT_VERSION}")
        if getattr(self.row_update, "lbl_sub", None):
            self.row_update.lbl_sub.setText("")
        self.btn_check_update.setText(t("btn_check_update"))
        if hasattr(self, "row_website"):
            self.row_website.lbl_title.setText(t("official_website", "官方网站"))
            self.btn_visit_site.setText(t("btn_visit_website", "🌐 访问官网"))
        if hasattr(self, "row_qq"):
            self.row_qq.lbl_title.setText(t("contact_qq", "联系作者 / QQ"))
            self.btn_copy_qq.setText(t("btn_copy_qq", "📋 复制"))
