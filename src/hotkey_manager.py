"""Luna Dimmer - HotkeyManager 门面 (Facade for Backward Compatibility)"""

from src.platform.hotkey_manager import (
    GlobalHotkeyManager,
    HotkeyManager,
    parse_hotkey_string,
    normalize_hotkey_string,
    test_hotkey_availability,
)

__all__ = [
    "GlobalHotkeyManager",
    "HotkeyManager",
    "parse_hotkey_string",
    "normalize_hotkey_string",
    "test_hotkey_availability",
]
