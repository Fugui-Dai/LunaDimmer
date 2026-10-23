"""Luna Dimmer - 集中式设计令牌与主题系统 (Design Tokens & Theming System)

遵循 Apple Human Interface Guidelines (macOS Sonoma / Sequoia / VisionOS):
集中管理 🌙 深色 (Dark Obsidian)、☀️ 浅色 (Snow White Porcelain)、💧 液态玻璃 (Liquid Glass Vibrancy)
三大 Apple 拟物视觉主题的设计令牌与物理色板。
"""

from typing import Dict, Any


class ThemeTokens:
    """设计令牌容器，提供各主题的标准色彩、渐变、边框与字体规范"""

    # 1. 🌙 深色主题 (Dark Theme - macOS Sonoma 沉浸黑曜石云石风格)
    DARK: Dict[str, Any] = {
        "name": "dark",
        "bg_window": "rgba(28, 28, 30, 0.90)",
        "bg_card": "rgba(36, 36, 38, 0.88)",
        "bg_inset": "rgba(20, 20, 22, 0.65)",
        "bg_sidebar": "rgba(24, 24, 26, 0.75)",
        "border_subtle": "rgba(255, 255, 255, 0.08)",
        "border_medium": "rgba(255, 255, 255, 0.14)",
        "border_card": "rgba(255, 255, 255, 0.12)",
        "border_rim": "rgba(255, 255, 255, 0.28)",
        "text_primary": "#FFFFFF",
        "text_secondary": "rgba(235, 235, 245, 0.65)",
        "text_tertiary": "rgba(235, 235, 245, 0.35)",
        "accent_primary": "#FF9F0A",         # Apple Night Shift / Amber Gold
        "accent_primary_hover": "#FFB340",
        "accent_secondary": "#0A84FF",       # Apple System Blue (Dark)
        "accent_emerald": "#30D158",         # Apple System Green (Dark)
        "accent_danger": "#FF453A",          # Apple System Red (Dark)
        "danger_bg": "rgba(255, 69, 58, 0.12)",
        "danger_border": "rgba(255, 69, 58, 0.35)",
        "shadow_card": "rgba(0, 0, 0, 0.45)",
        "track_bg": "rgba(0, 0, 0, 0.35)",
    }

    # 2. ☀️ 浅色主题 (Light Theme - macOS 白昼雪瓷毛玻璃风格)
    LIGHT: Dict[str, Any] = {
        "name": "light",
        "bg_window": "#F2F2F7",
        "bg_card": "#FFFFFF",
        "bg_inset": "rgba(0, 0, 0, 0.04)",
        "bg_sidebar": "rgba(242, 242, 247, 0.92)",
        "border_subtle": "rgba(0, 0, 0, 0.06)",
        "border_medium": "rgba(0, 0, 0, 0.12)",
        "border_card": "rgba(0, 0, 0, 0.09)",
        "border_rim": "rgba(255, 255, 255, 0.90)",
        "text_primary": "#1D1D1F",           # Apple Dark Charcoal
        "text_secondary": "rgba(60, 60, 67, 0.65)",
        "text_tertiary": "rgba(60, 60, 67, 0.35)",
        "accent_primary": "#FF9500",         # Apple Light Mode Amber
        "accent_primary_hover": "#E08500",
        "accent_secondary": "#007AFF",       # Apple System Blue (Light)
        "accent_emerald": "#34C759",         # Apple System Green (Light)
        "accent_danger": "#FF3B30",          # Apple System Red (Light)
        "danger_bg": "rgba(255, 59, 48, 0.08)",
        "danger_border": "rgba(255, 59, 48, 0.28)",
        "shadow_card": "rgba(0, 0, 0, 0.12)",
        "track_bg": "rgba(0, 0, 0, 0.06)",
    }

    # 3. 💧 液态玻璃主题 (Liquid Glass Theme - Apple VisionOS & Sequoia 高通透晶质微晶玻璃)
    LIQUID_GLASS: Dict[str, Any] = {
        "name": "liquid_glass",
        "bg_window": "rgba(22, 24, 32, 0.65)",
        "bg_card": "rgba(255, 255, 255, 0.08)",
        "bg_inset": "rgba(0, 0, 0, 0.25)",
        "bg_sidebar": "rgba(255, 255, 255, 0.05)",
        "border_subtle": "rgba(255, 255, 255, 0.12)",
        "border_medium": "rgba(255, 255, 255, 0.22)",
        "border_card": "rgba(255, 255, 255, 0.18)",
        "border_rim": "rgba(255, 255, 255, 0.55)",
        "text_primary": "#FFFFFF",
        "text_secondary": "rgba(235, 235, 245, 0.70)",
        "text_tertiary": "rgba(235, 235, 245, 0.40)",
        "accent_primary": "#0A84FF",         # Apple System Blue
        "accent_primary_hover": "#409CFF",
        "accent_secondary": "#5E5CE6",       # Apple System Indigo
        "accent_emerald": "#30D158",
        "accent_danger": "#FF453A",
        "danger_bg": "rgba(255, 69, 58, 0.15)",
        "danger_border": "rgba(255, 69, 58, 0.40)",
        "shadow_card": "rgba(0, 0, 0, 0.50)",
        "track_bg": "rgba(0, 0, 0, 0.40)",
    }

    @classmethod
    def get(cls, theme: str) -> Dict[str, Any]:
        """获取指定主题的设计令牌字典，默认降级为深色"""
        if theme == "light":
            return cls.LIGHT
        elif theme == "liquid_glass":
            return cls.LIQUID_GLASS
        return cls.DARK
