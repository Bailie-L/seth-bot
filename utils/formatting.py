"""
Standardized visual formatting for all Seth bot displays
"""

class SethVisuals:
    @staticmethod
    def health_bar(current, max_val):
        """Consistent health display across ALL commands"""
        percentage = (current / max_val) * 100
        filled = int(percentage / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        return f"{bar} {percentage:.0f}%"
    
    @staticmethod
    def hunger_bar(hunger):
        """Consistent stomach/hunger display"""
        fullness = 100 - hunger
        filled = int(fullness / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        return f"{bar} {fullness}% full (Hunger: {hunger})"
    
    @staticmethod
    def resource_bar(current, max_val, show_fraction=False):
        """Consistent resource display for inventory"""
        percentage = (current / max_val) * 100 if max_val > 0 else 0
        filled = int(percentage / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        if show_fraction:
            return f"{bar} {current}/{max_val}"
        return f"{bar} {percentage:.0f}%"

