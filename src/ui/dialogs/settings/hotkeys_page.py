"""Luna Dimmer - 设置中心：全局快捷键分页 (Hotkeys Page)

包含：
1. ACTION_KEY_MAP 配置键名映射字典；
2. HotkeyEditButton 实体物理防眩光录制键帽按钮；
3. HotkeysPage 8 个核心功能热键行、双向冲突自检与一键恢复默认。
"""

from typing import List
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from src.config import DEFAULT_CONFIG
from src.i18n import t
from src.hotkey_manager import (
    parse_hotkey_string,
    test_hotkey_availability,
)
from src.widgets.mac_controls import (
    MacInsetCard,
    MacSettingRow,
)

ACTION_KEY_MAP = {
    "hk_up": "brightness_up",
    "hk_down": "brightness_down",
    "hk_sleep": "toggle_sleep",
    "hk_stealth": "toggle_stealth",
    "hk_panel": "toggle_panel",
    "hk_settings": "open_settings",
    "hk_spotlight": "toggle_spotlight",
    "hk_emergency": "panic_restore",
}


class HotkeyEditButton(QFrame):
    """
    可交互录制全局快捷键键帽按钮（高对比度独立实体键帽，支持按键捕获、Esc取消、修饰键校验与双重冲突检测反馈）
    """
    sig_key_changed = pyqtSignal(str, str)  # (action_key, new_key_str)

    def __init__(self, action_key: str, current_key: str, is_emergency: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("hotkeyEditBtn")
        self.action_key = action_key
        self.current_key = current_key
        self.is_emergency = is_emergency
        self.is_recording = False
        self.parent_dialog = parent
        self._theme = "dark"

        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedHeight(28)
        self.setMinimumWidth(165)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)

        self.lbl_text = QLabel(self)
        self.lbl_text.setTextFormat(Qt.RichText)
        self.lbl_text.setAlignment(Qt.AlignCenter)
        self.lbl_text.setStyleSheet("border: none; background: transparent;")
        self.lbl_text.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.lbl_text)

        self._update_appearance()

    def set_theme(self, theme: str):
        if theme in ("dark", "light", "liquid_glass") and theme != getattr(self, "_theme", "dark"):
            self._theme = theme
            self._update_appearance()

    def _format_keycaps_html(self, key_str: str) -> str:
        if not key_str:
            empty_color = "rgba(60, 60, 67, 0.60)" if getattr(self, "_theme", "dark") == "light" else "rgba(235, 235, 245, 0.60)"
            return f'<span style="color: {empty_color}; font-size: 12px;">(未设置快捷键)</span>'
        display_str = key_str.replace("Up", "↑").replace("Down", "↓").replace("Left", "←").replace("Right", "→")
        parts = [p.strip() for p in display_str.split("+")]
        cur_th = getattr(self, "_theme", "dark")
        if cur_th == "light":
            color = "#FF9500" if self.is_emergency else "#1D1D1F"
            sep = '<span style="color: rgba(60, 60, 67, 0.45); font-size: 10.5px; font-weight: bold;"> + </span>'
        elif cur_th == "liquid_glass":
            color = "#FF9F0A" if self.is_emergency else "#FFFFFF"
            sep = '<span style="color: rgba(255, 255, 255, 0.45); font-size: 10.5px; font-weight: bold;"> + </span>'
        else:
            color = "#FF9F0A" if self.is_emergency else "#FFFFFF"
            sep = '<span style="color: rgba(235, 235, 245, 0.45); font-size: 10.5px; font-weight: bold;"> + </span>'
        tags = [
            f'<b style="color: {color}; font-size: 12.5px; font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, Consolas, \'Segoe UI\', sans-serif;">{p}</b>'
            for p in parts
        ]
        return sep.join(tags)

    def _update_appearance(self):
        cur_th = getattr(self, "_theme", "dark")
        if self.is_recording:
            if cur_th == "light":
                self.setStyleSheet("""
                    QFrame#hotkeyEditBtn {
                        background: rgba(255, 149, 0, 0.12);
                        border: 1.5px solid #FF9500;
                        border-radius: 6px;
                    }
                """)
                self.lbl_text.setText(f'<b style="font-size: 12px; font-weight: 700; color: #FF9500; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;">{t("hotkey_recording")}</b>')
            elif cur_th == "liquid_glass":
                self.setStyleSheet("""
                    QFrame#hotkeyEditBtn {
                        background: rgba(10, 132, 255, 0.20);
                        border: 1.5px solid #0A84FF;
                        border-radius: 6px;
                    }
                """)
                self.lbl_text.setText(f'<b style="font-size: 12px; font-weight: 700; color: #0A84FF; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;">{t("hotkey_recording")}</b>')
            else:
                self.setStyleSheet("""
                    QFrame#hotkeyEditBtn {
                        background: rgba(255, 159, 10, 0.18);
                        border: 1.5px solid #FF9F0A;
                        border-radius: 6px;
                    }
                """)
                self.lbl_text.setText(f'<b style="font-size: 12px; font-weight: 700; color: #FF9F0A; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;">{t("hotkey_recording")}</b>')
        else:
            if cur_th == "light":
                if self.is_emergency:
                    self.setStyleSheet("""
                        QFrame#hotkeyEditBtn {
                            background: rgba(255, 149, 0, 0.08);
                            border: 1px solid rgba(255, 149, 0, 0.35);
                            border-radius: 6px;
                        }
                        QFrame#hotkeyEditBtn:hover {
                            background: rgba(255, 149, 0, 0.16);
                            border-color: #FF9500;
                        }
                    """)
                else:
                    self.setStyleSheet("""
                        QFrame#hotkeyEditBtn {
                            background: rgba(0, 0, 0, 0.04);
                            border: 1px solid rgba(0, 0, 0, 0.10);
                            border-radius: 6px;
                        }
                        QFrame#hotkeyEditBtn:hover {
                            background: rgba(0, 0, 0, 0.08);
                            border-color: rgba(0, 0, 0, 0.20);
                        }
                    """)
            elif cur_th == "liquid_glass":
                if self.is_emergency:
                    self.setStyleSheet("""
                        QFrame#hotkeyEditBtn {
                            background: rgba(255, 159, 10, 0.15);
                            border: 1px solid rgba(255, 159, 10, 0.45);
                            border-top: 1px solid rgba(255, 255, 255, 0.40);
                            border-radius: 6px;
                        }
                        QFrame#hotkeyEditBtn:hover {
                            background: rgba(255, 159, 10, 0.26);
                            border-color: #FF9F0A;
                        }
                    """)
                else:
                    self.setStyleSheet("""
                        QFrame#hotkeyEditBtn {
                            background: rgba(255, 255, 255, 0.08);
                            border: 1px solid rgba(255, 255, 255, 0.18);
                            border-top: 1px solid rgba(255, 255, 255, 0.40);
                            border-radius: 6px;
                        }
                        QFrame#hotkeyEditBtn:hover {
                            background: rgba(255, 255, 255, 0.16);
                            border-color: rgba(255, 255, 255, 0.35);
                        }
                    """)
            else:
                if self.is_emergency:
                    self.setStyleSheet("""
                        QFrame#hotkeyEditBtn {
                            background: rgba(255, 159, 10, 0.14);
                            border: 1px solid rgba(255, 159, 10, 0.40);
                            border-radius: 6px;
                        }
                        QFrame#hotkeyEditBtn:hover {
                            background: rgba(255, 159, 10, 0.25);
                            border-color: #FF9F0A;
                        }
                    """)
                else:
                    self.setStyleSheet("""
                        QFrame#hotkeyEditBtn {
                            background: rgba(255, 255, 255, 0.06);
                            border: 1px solid rgba(255, 255, 255, 0.12);
                            border-radius: 6px;
                        }
                        QFrame#hotkeyEditBtn:hover {
                            background: rgba(255, 255, 255, 0.12);
                            border-color: rgba(255, 255, 255, 0.25);
                        }
                    """)
            self.lbl_text.setText(self._format_keycaps_html(self.current_key))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.is_recording:
                self.start_recording()
            event.accept()
        else:
            super().mousePressEvent(event)

    def start_recording(self):
        handler = getattr(self.parent_dialog, "stop_all_hotkey_recordings", None)
        if not handler and hasattr(self.parent_dialog, "hotkeys_page"):
            handler = getattr(self.parent_dialog.hotkeys_page, "stop_all_hotkey_recordings", None)
        if handler:
            handler(exclude=self)
        self.is_recording = True
        self.setFocus()
        self._update_appearance()

    def stop_recording(self):
        self.is_recording = False
        self._update_appearance()

    def focusOutEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()

        # 按 Esc 取消当前按键录制
        if key == Qt.Key_Escape:
            self.stop_recording()
            if hasattr(self.parent_dialog, "show_hotkey_status"):
                self.parent_dialog.show_hotkey_status(t("hotkey_recording_canceled", "已取消按键修改"), is_error=False)
            event.accept()
            return

        # 忽略单纯的修饰键按下
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            event.accept()
            return

        modifiers = event.modifiers()
        has_ctrl = bool(modifiers & Qt.ControlModifier)
        has_alt = bool(modifiers & Qt.AltModifier)
        has_shift = bool(modifiers & Qt.ShiftModifier)

        # 校验必须包含至少一个修饰键
        if not (has_ctrl or has_alt):
            if hasattr(self.parent_dialog, "show_hotkey_status"):
                self.parent_dialog.show_hotkey_status(t("hotkey_invalid_mod"), is_error=True)
            event.accept()
            return

        # 映射键名
        key_str = ""
        if Qt.Key_A <= key <= Qt.Key_Z:
            key_str = chr(key)
        elif Qt.Key_0 <= key <= Qt.Key_9:
            key_str = chr(key)
        elif key == Qt.Key_Up:
            key_str = "Up"
        elif key == Qt.Key_Down:
            key_str = "Down"
        elif key == Qt.Key_Left:
            key_str = "Left"
        elif key == Qt.Key_Right:
            key_str = "Right"
        elif key == Qt.Key_Backspace:
            key_str = "Backspace"
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            key_str = "Return"
        elif key == Qt.Key_Space:
            key_str = "Space"
        elif Qt.Key_F1 <= key <= Qt.Key_F12:
            key_str = f"F{key - Qt.Key_F1 + 1}"
        else:
            event.accept()
            return

        # 组装快捷键字符串
        parts = []
        if has_ctrl:
            parts.append("Ctrl")
        if has_alt:
            parts.append("Alt")
        if has_shift:
            parts.append("Shift")
        parts.append(key_str)
        candidate_key = "+".join(parts)

        # 1. 软件内部快捷键冲突自检
        if hasattr(self.parent_dialog, "check_internal_conflict"):
            conflicted_action = self.parent_dialog.check_internal_conflict(self.action_key, candidate_key)
            if conflicted_action:
                action_name = t(conflicted_action)
                msg = t("hotkey_conflict_internal").replace("{action}", action_name)
                if hasattr(self.parent_dialog, "show_hotkey_status"):
                    self.parent_dialog.show_hotkey_status(msg, is_error=True)
                event.accept()
                return

        # 2. Windows 真实系统注册可用性检测（带上原键位，避免把自己已注册的键误判为被占用）
        can_register, err_msg = test_hotkey_availability(candidate_key, self.current_key)
        if not can_register:
            if "1409" in err_msg or "占用" in err_msg:
                msg = t("hotkey_conflict_win32")
            else:
                msg = f"⚠️ 快捷键无法使用: {err_msg}"
            if hasattr(self.parent_dialog, "show_hotkey_status"):
                self.parent_dialog.show_hotkey_status(msg, is_error=True)
            event.accept()
            return

        # 校验成功！应用新按键
        self.current_key = candidate_key
        self.stop_recording()
        if hasattr(self.parent_dialog, "show_hotkey_status"):
            msg = t("hotkey_set_success").replace("{key}", candidate_key)
            self.parent_dialog.show_hotkey_status(msg, is_error=False)
        self.sig_key_changed.emit(self.action_key, candidate_key)
        event.accept()

class HotkeysPage(QWidget):
    """全局快捷键录制与冲突检测偏好设置页面"""

    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog
        self.config = parent_dialog.config
        self.hotkey_buttons: List[HotkeyEditButton] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 头部标题与一键恢复快捷键按钮
        hdr_widget = QWidget(self)
        hdr_layout = QHBoxLayout(hdr_widget)
        hdr_layout.setContentsMargins(2, 0, 2, 0)

        self.lbl_hk_title = QLabel(t("tab_hotkeys"), hdr_widget)
        self.lbl_hk_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        hdr_layout.addWidget(self.lbl_hk_title)
        hdr_layout.addStretch()

        self.btn_reset_hotkeys = QPushButton(t("btn_reset_hotkeys"), hdr_widget)
        self.btn_reset_hotkeys.setCursor(Qt.PointingHandCursor)
        self.btn_reset_hotkeys.setFixedHeight(24)
        self.btn_reset_hotkeys.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 1px 10px;
                font-size: 12px;
                font-weight: 500;
                color: #94A3B8;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.14);
                color: #FFFFFF;
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        # 注意：clicked 会带一个 bool 参数，必须用 lambda 包一层，
        # 否则 False 会被当成 reset_only_hotkeys(reload_runtime=...) 而跳过运行时热重载。
        self.btn_reset_hotkeys.clicked.connect(lambda: self.reset_only_hotkeys())
        hdr_layout.addWidget(self.btn_reset_hotkeys)
        layout.addWidget(hdr_widget)

        # 快捷键卡片 (8项核心功能)
        self.card_hk = MacInsetCard(self)
        # (action_key, 标题 i18n key, 描述 i18n key) —— 同时保留键名以便切语言时整页重绘
        hotkey_items = [
            ("hk_up", "hk_up", "hk_up_sub"),
            ("hk_down", "hk_down", "hk_down_sub"),
            ("hk_sleep", "hk_sleep", "hk_sleep_sub"),
            ("hk_stealth", "hk_stealth", "hk_stealth_sub"),
            ("hk_spotlight", "hk_spotlight", "hk_spotlight_sub"),
            ("hk_panel", "hk_panel", "hk_panel_sub"),
            ("hk_settings", "hk_settings", "hk_settings_sub"),
            ("hk_emergency", "hk_emergency", "hk_emergency_sub"),
        ]

        saved_hotkeys = self.config.get_hotkeys()
        default_hotkeys = DEFAULT_CONFIG["hotkeys"]
        self._hotkey_rows = []

        for idx, (action_key, title_key, sub_key) in enumerate(hotkey_items):
            conf_key = ACTION_KEY_MAP.get(action_key, action_key)
            current_key = saved_hotkeys.get(conf_key, default_hotkeys.get(conf_key, "Ctrl+Alt+None"))
            is_emergency = (action_key == "hk_emergency")

            btn = HotkeyEditButton(action_key, current_key, is_emergency=is_emergency, parent=self.parent_dialog)
            btn.sig_key_changed.connect(self._on_hotkey_changed)
            self.hotkey_buttons.append(btn)

            row = MacSettingRow(
                t(title_key), t(sub_key), btn,
                is_last=(idx == len(hotkey_items) - 1),
                parent=self.card_hk,
            )
            self.card_hk.add_row(row)
            self._hotkey_rows.append((row, title_key, sub_key))

        layout.addWidget(self.card_hk)

        # 底部状态反馈提示栏
        self.lbl_hk_status = QLabel("", self)
        self.lbl_hk_status.setStyleSheet("font-size: 12.5px; font-weight: 500; color: #94A3B8; padding-left: 4px;")
        layout.addWidget(self.lbl_hk_status)

        layout.addStretch()

    def _on_hotkey_changed(self, action_key: str, new_key: str):
        """快捷键录制成功后持久化并热重载运行时监听；注册失败则回滚配置（保持单一真相源）"""
        conf_key = ACTION_KEY_MAP.get(action_key, action_key)
        previous_hotkeys = self.config.get_hotkeys()
        hotkeys = dict(previous_hotkeys)
        hotkeys[conf_key] = new_key
        self.config.set_hotkeys(hotkeys)

        parent_win = self.parent_dialog.parent() if self.parent_dialog else None
        registered = True
        if parent_win and hasattr(parent_win, "reload_hotkeys"):
            try:
                result = parent_win.reload_hotkeys()
                registered = True if result is None else bool(result)
            except Exception:
                registered = False

        if not registered:
            # 运行时仍保留旧键位，配置也必须回到旧键位，避免下次启动绑定失败
            self.config.set_hotkeys(previous_hotkeys)
            self.show_hotkey_status(t("hotkey_register_failed", "⚠️ 快捷键注册失败，已保留原键位"), is_error=True)
            return

        self.config.save()

    def show_hotkey_status(self, msg: str, is_error: bool = False):
        color = "#F87171" if is_error else "#34D399"
        self.lbl_hk_status.setStyleSheet(f"font-size: 12.5px; font-weight: 600; color: {color}; padding-left: 4px;")
        self.lbl_hk_status.setText(msg)
        if not is_error:
            QTimer.singleShot(3500, lambda: self.lbl_hk_status.setText("") if self.lbl_hk_status else None)

    def stop_all_hotkey_recordings(self, exclude=None):
        for btn in self.hotkey_buttons:
            if btn is not exclude and getattr(btn, "is_recording", False):
                btn.stop_recording()

    def check_internal_conflict(self, current_action_key: str, candidate_key: str):
        try:
            cand_mods, cand_vk = parse_hotkey_string(candidate_key)
        except Exception:
            return None

        for btn in self.hotkey_buttons:
            if btn.action_key == current_action_key:
                continue
            try:
                b_mods, b_vk = parse_hotkey_string(btn.current_key)
                if (cand_mods, cand_vk) == (b_mods, b_vk):
                    return btn.action_key
            except Exception:
                continue
        return None

    def reset_only_hotkeys(self, reload_runtime: bool = True):
        """
        恢复全部默认快捷键：UI 键帽、配置文件与**运行时监听**三者同时生效。

        旧实现只改了按钮文案（既不落盘也不重新注册），用户必须重启才生效。
        """
        default_hotkeys = DEFAULT_CONFIG["hotkeys"]
        for btn in self.hotkey_buttons:
            conf_key = ACTION_KEY_MAP.get(btn.action_key, btn.action_key)
            if conf_key in default_hotkeys:
                btn.current_key = default_hotkeys[conf_key]
                btn._update_appearance()

        self.config.set_hotkeys(default_hotkeys)
        self.config.save()

        if reload_runtime:
            parent_win = self.parent_dialog.parent() if self.parent_dialog else None
            if parent_win and hasattr(parent_win, "reload_hotkeys"):
                try:
                    parent_win.reload_hotkeys()
                except Exception:
                    pass

        self.show_hotkey_status(t("hotkeys_reset_done"), is_error=False)

    def apply_theme(self, theme: str):
        self.card_hk.apply_theme(theme)
        for btn in self.hotkey_buttons:
            btn._theme = theme
            btn._update_appearance()

        if theme == "light":
            self.lbl_hk_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1D1D1F;")
            self.btn_reset_hotkeys.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 6px;
                    padding: 1px 10px;
                    font-size: 12px;
                    font-weight: 500;
                    color: #1D1D1F;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.09);
                    border-color: rgba(0, 0, 0, 0.20);
                }
                QPushButton:pressed {
                    background: rgba(0, 0, 0, 0.14);
                }
            """)
        elif theme == "liquid_glass":
            self.lbl_hk_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
            self.btn_reset_hotkeys.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-radius: 6px;
                    padding: 1px 10px;
                    font-size: 12px;
                    font-weight: 500;
                    color: #FFFFFF;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.16);
                    border-color: rgba(255, 255, 255, 0.35);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.22);
                }
            """)
        else:
            self.lbl_hk_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
            self.btn_reset_hotkeys.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 6px;
                    padding: 1px 10px;
                    font-size: 12px;
                    font-weight: 500;
                    color: #F5F5F7;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.12);
                    border-color: rgba(255, 255, 255, 0.25);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.18);
                }
            """)

    def retranslate(self):
        self.lbl_hk_title.setText(t("tab_hotkeys"))
        self.btn_reset_hotkeys.setText(t("btn_reset_hotkeys"))
        for row, title_key, sub_key in getattr(self, "_hotkey_rows", []):
            row.lbl_title.setText(t(title_key))
            row.lbl_sub.setText(t(sub_key))
