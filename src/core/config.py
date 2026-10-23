"""Luna Dimmer - 全局配置管理与 JSON 持久化中心 (Configuration & Persistence)

工程保障：
1. 原子落盘：先写入 `.tmp` 再 `os.replace`，杜绝断电/强杀导致的半截 JSON；
2. 自动备份与自愈：写入前滚动保留 `.bak`，主文件损坏时自动从备份恢复；
3. 永不抛异常：任何磁盘异常仅记录日志，绝不让 Qt 槽函数因 IO 失败而崩溃；
4. 深度合并：旧版配置缺失的新字段自动补齐，快捷键与场景预设逐项合并。
"""

import copy
import json
import logging
import os
import shutil
from typing import Any, Dict, Optional

from src.services.i18n import get_system_default_language

logger = logging.getLogger("LunaConfig")

DEFAULT_SCENE_PRESETS: Dict[str, Any] = {
    "work": {
        "name": "白天办公",
        "icon": "☀️",
        "brightness": 90,
        "warmth": 0,
        "boost_2x": False,
    },
    "night": {
        "name": "夜间阅读",
        "icon": "🌙",
        "brightness": 30,
        "warmth": 45,
        "boost_2x": False,
    },
    "sleep": {
        "name": "睡前极暗",
        "icon": "🛌",
        "brightness": 5,
        "warmth": 70,
        "boost_2x": True,
    },
    "noon": {
        "name": "午间休息",
        "icon": "☕",
        "brightness": 65,
        "warmth": 25,
        "boost_2x": False,
    },
    "custom_1": {
        "name": "自定义 1",
        "icon": "🎨",
        "brightness": 50,
        "warmth": 35,
        "boost_2x": False,
    },
    "custom_2": {
        "name": "自定义 2",
        "icon": "🌟",
        "brightness": 20,
        "warmth": 55,
        "boost_2x": False,
    },
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "brightness": None,  # 首次启动为 None：默认读取并遵循屏幕真实物理亮度；用户调节后持久化保存
    "warmth": 0,
    "enhanced_2x": False,
    "remember_window_position": True,
    "window_pos": None,
    "auto_update": True,
    "smooth_wake": True,
    "theme": "dark",
    "language": get_system_default_language(),
    "autostart": False,
    "fullscreen_guard": True,
    "hotkeys": {
        "brightness_up": "Ctrl+Alt+Up",
        "brightness_down": "Ctrl+Alt+Down",
        "toggle_sleep": "Ctrl+Alt+S",
        "toggle_stealth": "Ctrl+Alt+B",
        "toggle_panel": "Ctrl+Alt+L",
        "open_settings": "Ctrl+Alt+P",
        "toggle_spotlight": "Ctrl+Alt+F",
        "panic_restore": "Ctrl+Alt+Backspace",
    },
    "scene_presets": copy.deepcopy(DEFAULT_SCENE_PRESETS),
}


class ConfigManager:
    def __init__(self, filepath: str = None):
        if filepath is None:
            appdata = os.getenv("APPDATA", os.path.expanduser("~"))
            target_dir = os.path.join(appdata, "LunaDimmer")
            os.makedirs(target_dir, exist_ok=True)
            self.filepath = os.path.join(target_dir, "config.json")
        else:
            self.filepath = filepath
        self._data: Dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    # ------------------------------------------------------------------
    # 基础读写
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    @staticmethod
    def _read_json_dict(filepath: str) -> Optional[Dict[str, Any]]:
        """安全地读取一个 JSON 对象，任何异常（缺失/损坏/类型不符）均返回 None"""
        try:
            if not os.path.exists(filepath):
                return None
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except Exception as e:
            logger.warning("读取配置文件失败 %s: %s", filepath, e)
            return None

    def _merge_saved(self, saved: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并旧版配置：补齐新增快捷键，逐项合并场景预设，兼容历史字段名"""
        merged = copy.deepcopy(saved)

        if isinstance(saved.get("hotkeys"), dict):
            merged_hk = copy.deepcopy(DEFAULT_CONFIG["hotkeys"])
            merged_hk.update(saved["hotkeys"])
            merged["hotkeys"] = merged_hk

        if isinstance(saved.get("scene_presets"), dict):
            merged_sp = copy.deepcopy(DEFAULT_SCENE_PRESETS)
            for k, v in saved["scene_presets"].items():
                if isinstance(v, dict):
                    if k in merged_sp:
                        merged_sp[k].update(v)
                    else:
                        merged_sp[k] = v
            merged["scene_presets"] = merged_sp
        elif isinstance(saved.get("custom_presets"), dict):
            merged_sp = copy.deepcopy(DEFAULT_SCENE_PRESETS)
            for k, v in saved["custom_presets"].items():
                if isinstance(v, dict) and k in merged_sp:
                    merged_sp[k].update(v)
            merged["scene_presets"] = merged_sp

        return merged

    def load(self) -> None:
        """加载配置；主文件损坏时自动回退到 .bak 备份并重建主文件"""
        self._data = copy.deepcopy(DEFAULT_CONFIG)

        saved = self._read_json_dict(self.filepath)
        if saved is None and os.path.exists(self.filepath):
            backup_path = self.filepath + ".bak"
            saved = self._read_json_dict(backup_path)
            if saved is not None:
                logger.warning("主配置文件损坏，已从备份恢复: %s", backup_path)
                self._data.update(self._merge_saved(saved))
                self.save()
                return
            logger.error("配置文件与其备份均不可读，已回退出厂默认设置: %s", self.filepath)
            return

        if saved is not None:
            self._data.update(self._merge_saved(saved))

    def save(self) -> bool:
        """原子持久化写入：`.tmp` → fsync → 滚动 `.bak` → `os.replace`，永不抛异常"""
        target_dir = os.path.dirname(os.path.abspath(self.filepath))
        tmp_path = self.filepath + ".tmp"
        backup_path = self.filepath + ".bak"
        try:
            os.makedirs(target_dir, exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
            if os.path.exists(self.filepath):
                try:
                    shutil.copy2(self.filepath, backup_path)
                except OSError:
                    pass
            os.replace(tmp_path, self.filepath)
            return True
        except Exception as e:
            logger.error("写入配置文件失败 %s: %s", self.filepath, e)
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            return False

    def reset_to_defaults(self) -> None:
        """重置所有设置为出厂默认配置并持久化写入磁盘"""
        self._data = copy.deepcopy(DEFAULT_CONFIG)
        self.save()

    # ------------------------------------------------------------------
    # 便捷访问器
    # ------------------------------------------------------------------
    def get_hotkeys(self) -> Dict[str, str]:
        """返回当前快捷键映射（始终包含全部已知动作键）"""
        merged = copy.deepcopy(DEFAULT_CONFIG["hotkeys"])
        saved = self._data.get("hotkeys")
        if isinstance(saved, dict):
            merged.update({k: v for k, v in saved.items() if isinstance(v, str) and v.strip()})
        return merged

    def set_hotkeys(self, hotkeys: Dict[str, str]) -> None:
        merged = copy.deepcopy(DEFAULT_CONFIG["hotkeys"])
        if isinstance(hotkeys, dict):
            merged.update({k: v for k, v in hotkeys.items() if isinstance(v, str) and v.strip()})
        self._data["hotkeys"] = merged

    def get_scene_presets(self) -> Dict[str, Any]:
        """返回完整的 6 大场景预设（缺失项自动回填出厂值）"""
        merged = copy.deepcopy(DEFAULT_SCENE_PRESETS)
        saved = self._data.get("scene_presets")
        if isinstance(saved, dict):
            for k, v in saved.items():
                if isinstance(v, dict) and k in merged:
                    merged[k].update(v)
                elif isinstance(v, dict):
                    merged[k] = v
        return merged

    def set_scene_presets(self, presets: Dict[str, Any]) -> None:
        self._data["scene_presets"] = copy.deepcopy(presets)
