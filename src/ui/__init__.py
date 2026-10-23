"""Luna Dimmer - UI 表现层模块 (Presentation Layer)

性能与稳定性约定：本包**不做急切导入**。
`src.ui.dialogs.*` 与 `src.widgets.*` 之间存在正常的双向引用，
若在包初始化时急切导入 `src.ui.main_window`，极易在冷启动阶段形成
「半初始化模块」的循环导入；改为 PEP 562 惰性导出后彻底消除该风险。
"""

from typing import Any, Dict, Tuple

_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "LunaMainWindow": ("src.ui.main_window", "LunaMainWindow"),
    "MainWindow": ("src.ui.main_window", "MainWindow"),
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
