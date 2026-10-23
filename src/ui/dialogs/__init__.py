"""Luna Dimmer - 统一弹窗模块 (Dialogs Module)

集中管理与导出所有窗口层与偏好设置对话框：
- SettingsDialog: 苹果 macOS 拟物系统偏好设置中心；
- SponsorDialog: 昼夜节律心意赞赏信笺；
- FeedbackDialog: 安全防刷人机验证反馈弹窗；
- PresetCustomizerDialog: 场景预设可视化管理与调控中心。
"""

from src.ui.dialogs.settings import SettingsDialog
from src.ui.dialogs.sponsor_dialog import SponsorDialog
from src.ui.dialogs.feedback_dialog import FeedbackDialog
from src.ui.dialogs.preset_dialog import PresetCustomizerDialog

__all__ = [
    "SettingsDialog",
    "SponsorDialog",
    "FeedbackDialog",
    "PresetCustomizerDialog",
]
