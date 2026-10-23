"""Luna Dimmer - 系统设置中心模块 (Settings Dialog Module)"""

from src.ui.dialogs.settings.settings_dialog import SettingsDialog
from src.ui.dialogs.settings.hotkeys_page import HotkeyEditButton, ACTION_KEY_MAP
from src.ui.dialogs.settings.general_page import GeneralPage
from src.ui.dialogs.settings.optics_page import OpticsPage
from src.ui.dialogs.settings.hotkeys_page import HotkeysPage
from src.ui.dialogs.settings.safety_page import SafetyPage

__all__ = [
    "SettingsDialog",
    "HotkeyEditButton",
    "ACTION_KEY_MAP",
    "GeneralPage",
    "OpticsPage",
    "HotkeysPage",
    "SafetyPage",
]
