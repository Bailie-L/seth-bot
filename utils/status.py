"""Pure helper functions for Seth status calculations"""
from config import (
    HEALTH_EXCELLENT_THRESHOLD, HEALTH_GOOD_THRESHOLD,
    HEALTH_FAIR_THRESHOLD, HEALTH_POOR_THRESHOLD,
    HUNGER_SATISFIED_THRESHOLD, HUNGER_PECKISH_THRESHOLD,
    HUNGER_HUNGRY_THRESHOLD, HUNGER_STARVING_THRESHOLD,
    HEALTH_COLOR_GREEN_THRESHOLD, HEALTH_COLOR_RED_THRESHOLD,
)

# Color values matching discord.Color presets
COLOR_GREEN = 0x2ecc71
COLOR_YELLOW = 0xf1c40f
COLOR_RED = 0xe74c3c


def get_health_status(health):
    """Get status text for health value"""
    if health >= HEALTH_EXCELLENT_THRESHOLD:
        return "EXCELLENT"
    elif health >= HEALTH_GOOD_THRESHOLD:
        return "GOOD"
    elif health >= HEALTH_FAIR_THRESHOLD:
        return "FAIR"
    elif health >= HEALTH_POOR_THRESHOLD:
        return "POOR"
    else:
        return "CRITICAL"


def get_hunger_status(hunger):
    """Get status text for hunger value"""
    if hunger <= HUNGER_SATISFIED_THRESHOLD:
        return "SATISFIED"
    elif hunger <= HUNGER_PECKISH_THRESHOLD:
        return "PECKISH"
    elif hunger <= HUNGER_HUNGRY_THRESHOLD:
        return "HUNGRY"
    elif hunger <= HUNGER_STARVING_THRESHOLD:
        return "STARVING"
    else:
        return "DESPERATE"


def get_health_color(health):
    """Get embed color int based on health"""
    if health > HEALTH_COLOR_GREEN_THRESHOLD:
        return COLOR_GREEN
    elif health > HEALTH_COLOR_RED_THRESHOLD:
        return COLOR_YELLOW
    else:
        return COLOR_RED
