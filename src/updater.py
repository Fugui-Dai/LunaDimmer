"""Luna Dimmer - Updater 门面 (Facade for Backward Compatibility)"""

from src.services.updater import (
    CURRENT_VERSION,
    DEFAULT_UPDATE_METADATA_URL,
    UpdateWorker,
    DownloadWorker,
    UpgradeDialog,
    apply_update_and_restart,
    is_newer_version,
    parse_version_tuple,
)

__all__ = [
    "CURRENT_VERSION",
    "DEFAULT_UPDATE_METADATA_URL",
    "UpdateWorker",
    "DownloadWorker",
    "UpgradeDialog",
    "apply_update_and_restart",
    "is_newer_version",
    "parse_version_tuple",
]
