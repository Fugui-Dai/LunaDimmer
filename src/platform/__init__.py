"""Luna Dimmer - 操作系统底层适配器模块 (Platform Layer)

封装 Windows Win32 API 原生互操作与全局热键机制：
- win32_compat: DXVA2, GDI32, User32 底层硬件调光与窗口控制；
- hotkey_manager: Win32 全局热键 Hook 与后台消息泵。
"""

from src.platform.win32_compat import *
from src.platform.hotkey_manager import HotkeyManager, parse_hotkey_string, normalize_hotkey_string

__all__ = [
    "HotkeyManager",
    "parse_hotkey_string",
    "normalize_hotkey_string",
]
