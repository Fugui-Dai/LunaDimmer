"""Luna Dimmer - i18n 门面 (Facade for Backward Compatibility)"""

from src.services.i18n import (
    t,
    get_language,
    set_language,
    get_system_default_language,
    TRANSLATIONS,
)

__all__ = [
    "t",
    "get_language",
    "set_language",
    "get_system_default_language",
    "TRANSLATIONS",
]
