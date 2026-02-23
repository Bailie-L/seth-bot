"""
Standardized visual formatting for all Seth bot displays
"""
from config import BAR_SEGMENTS, BAR_PERCENTAGE_MAX


class SethVisuals:
    @staticmethod
    def health_bar(current: int, max_val: int) -> str:
        """Consistent health display across ALL commands"""
        percentage = (current / max_val) * BAR_PERCENTAGE_MAX
        filled = int(percentage / BAR_SEGMENTS)
        empty = BAR_SEGMENTS - filled
        bar = "█" * filled + "░" * empty
        return f"{bar} {percentage:.0f}%"

    @staticmethod
    def hunger_bar(hunger: int) -> str:
        """Consistent stomach/hunger display"""
        fullness = BAR_PERCENTAGE_MAX - hunger
        filled = int(fullness / BAR_SEGMENTS)
        empty = BAR_SEGMENTS - filled
        bar = "█" * filled + "░" * empty
        return f"{bar} {fullness}% full (Hunger: {hunger})"

    @staticmethod
    def resource_bar(current: int, max_val: int, show_fraction: bool = False) -> str:
        """Consistent resource display for inventory"""
        percentage = (current / max_val) * BAR_PERCENTAGE_MAX if max_val > 0 else 0
        filled = int(percentage / BAR_SEGMENTS)
        empty = BAR_SEGMENTS - filled
        bar = "█" * filled + "░" * empty
        if show_fraction:
            return f"{bar} {current}/{max_val}"
        return f"{bar} {percentage:.0f}%"
