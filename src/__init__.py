"""Luna Dimmer - 官方现代化分层架构包 (Clean Layered Architecture)

模块分层规范：
- core: 调光引擎、全屏分层遮罩、崩溃守护、配置实体；
- platform: Win32 原生互操作、底层全局热键 Hook 消息泵；
- ui: 主控制面板、弹窗中心 (Settings, Sponsor, Feedback, Preset)、基础控件库；
- styles: 集中式设计令牌 (ThemeTokens) 与程序图标绘制；
- services: 国际化本地化字典、版本在线检测。

性能约定：
本包 **不做任何急切导入**。`import src.core.config` 这类底层调用不应连带拉起 PyQt5
与整个 UI 栈（否则崩溃守护子进程会被拖成重型 GUI 进程，冷启动也会明显变慢）。
所有历史顶层导出改由 PEP 562 的模块级 `__getattr__` 惰性提供，行为与旧版 `from src import X` 完全一致。
"""

from typing import Any, Dict, Tuple

# 顶层惰性导出表：属性名 -> (子模块路径, 子模块内属性名)
_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "BrightnessEngine": ("src.core.brightness_engine", "BrightnessEngine"),
    "OverlayWindow": ("src.core.overlay_window", "OverlayWindow"),
    "SleepDimmerOverlay": ("src.core.overlay_window", "SleepDimmerOverlay"),
    "ConfigManager": ("src.core.config", "ConfigManager"),
    "LunaMainWindow": ("src.ui.main_window", "LunaMainWindow"),
    "MainWindow": ("src.ui.main_window", "MainWindow"),
    "ThemeTokens": ("src.styles.tokens", "ThemeTokens"),
    "create_app_icon": ("src.styles.app_icon", "create_app_icon"),
    "t": ("src.services.i18n", "t"),
    "get_language": ("src.services.i18n", "get_language"),
    "set_language": ("src.services.i18n", "set_language"),
    "CURRENT_VERSION": ("src.services.updater", "CURRENT_VERSION"),
}


def __getattr__(name: str) -> Any:
    """PEP 562：仅在真正访问时才导入对应子模块，避免包初始化时的重型副作用"""
    try:
        module_path, attr_name = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None

    import importlib

    module = importlib.import_module(module_path)
    value = getattr(module, attr_name)
    globals()[name] = value  # 缓存，后续访问直接命中
    return value


def __dir__():
    return sorted(set(list(globals().keys()) + list(_LAZY_EXPORTS.keys())))


__all__ = list(_LAZY_EXPORTS.keys())
