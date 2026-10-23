"""Luna Dimmer - SettingsDialog 模块门面 (Facade for Backward Compatibility)

遵循大厂架构规范：
1. 底层实现已全面解耦迁移至 src/ui/dialogs/settings/ 模块化子包；
2. 本文件保留所有公开类与常量的透明重导出，确保现有调用与测试 100% 零修改平滑过渡。
"""

from src.ui.dialogs.settings import (
    SettingsDialog,
    HotkeyEditButton,
    ACTION_KEY_MAP,
    GeneralPage,
    OpticsPage,
    HotkeysPage,
    SafetyPage,
)

__all__ = [
    "SettingsDialog",
    "HotkeyEditButton",
    "ACTION_KEY_MAP",
    "GeneralPage",
    "OpticsPage",
    "HotkeysPage",
    "SafetyPage",
]
