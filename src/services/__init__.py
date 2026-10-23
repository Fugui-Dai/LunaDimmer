"""Luna Dimmer - 跨领域公共服务模块 (Services Layer)

包含：
- i18n: 中英双语国际化服务；
- updater: GitHub Release 检查与版本热更新服务。

性能约定：本包**不做急切导入**，避免业务层仅需翻译函数时却拉起 UpdateWorker 的 PyQt 依赖。
"""

from typing import Any, Dict, Tuple

_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "t": ("src.services.i18n", "t"),
    "get_language": ("src.services.i18n", "get_language"),
    "set_language": ("src.services.i18n", "set_language"),
    "get_system_default_language": ("src.services.i18n", "get_system_default_language"),
    "CURRENT_VERSION": ("src.services.updater", "CURRENT_VERSION"),
    "UpdateWorker": ("src.services.updater", "UpdateWorker"),
    "UpgradeDialog": ("src.services.updater", "UpgradeDialog"),
    "is_newer_version": ("src.services.updater", "is_newer_version"),
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
