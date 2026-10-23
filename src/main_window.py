"""Luna Dimmer - MainWindow 模块门面 (Facade for Backward Compatibility)

遵循大厂架构规范：
1. 界面实现已迁移至 src/ui/main_window.py；
2. 本门面保留 LunaMainWindow 与 MainWindow 的透明导出，确保 main.py 与外部调用 100% 兼容。
"""

from src.ui.main_window import LunaMainWindow

MainWindow = LunaMainWindow

__all__ = ["LunaMainWindow", "MainWindow"]
