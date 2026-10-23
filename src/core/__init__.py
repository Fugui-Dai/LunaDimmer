"""Luna Dimmer - 业务与调光核心域 (Core Domain)

包含：
- BrightnessEngine: 物理 DDC/CI 通道与软件遮罩双轨衰减协调器；
- SleepDimmerOverlay / OverlayWindow: 极限 1% 微光透明分层穿透窗口；
- run_guard, restore_screen: 崩溃安全守护与满亮复原机制；
- ConfigManager, DEFAULT_CONFIG, DEFAULT_SCENE_PRESETS: 配置持久化与场景预设。

性能约定：本包**不做急切导入**。崩溃守护子进程只需 `crash_guard`，
不应因为 `import src.core` 而连带加载 PyQt 遮罩窗口模块。
"""

from typing import Any, Dict, Tuple

_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "BrightnessEngine": ("src.core.brightness_engine", "BrightnessEngine"),
    "SleepDimmerOverlay": ("src.core.overlay_window", "SleepDimmerOverlay"),
    "OverlayWindow": ("src.core.overlay_window", "OverlayWindow"),
    "run_guard": ("src.core.crash_guard", "run_guard"),
    "restore_screen": ("src.core.crash_guard", "restore_screen"),
    "ConfigManager": ("src.core.config", "ConfigManager"),
    "DEFAULT_CONFIG": ("src.core.config", "DEFAULT_CONFIG"),
    "DEFAULT_SCENE_PRESETS": ("src.core.config", "DEFAULT_SCENE_PRESETS"),
}


def __getattr__(name: str) -> Any:
    try:
        module_path, attr_name = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None

    import importlib

    value = getattr(importlib.import_module(module_path), attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(list(globals().keys()) + list(_LAZY_EXPORTS.keys())))


__all__ = list(_LAZY_EXPORTS.keys())
