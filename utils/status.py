"""Pure helper functions for Seth status calculations"""

# Color values matching discord.Color presets
COLOR_GREEN = 0x2ecc71
COLOR_YELLOW = 0xf1c40f
COLOR_RED = 0xe74c3c


def get_health_status(health):
    """Get status text for health value"""
    if health >= 80:
        return "EXCELLENT"
    elif health >= 60:
        return "GOOD"
    elif health >= 40:
        return "FAIR"
    elif health >= 20:
        return "POOR"
    else:
        return "CRITICAL"


def get_hunger_status(hunger):
    """Get status text for hunger value"""
    if hunger <= 20:
        return "SATISFIED"
    elif hunger <= 40:
        return "PECKISH"
    elif hunger <= 60:
        return "HUNGRY"
    elif hunger <= 80:
        return "STARVING"
    else:
        return "DESPERATE"


def get_health_color(health):
    """Get embed color int based on health"""
    if health > 70:
        return COLOR_GREEN
    elif health > 30:
        return COLOR_YELLOW
    else:
        return COLOR_RED
