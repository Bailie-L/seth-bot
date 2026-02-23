"""Tests for Seth status helper functions (utils/status.py)"""
from utils.status import (
    get_health_status, get_hunger_status, get_health_color,
    COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
)


class TestGetHealthStatus:
    def test_excellent(self):
        assert get_health_status(100) == "EXCELLENT"
        assert get_health_status(80) == "EXCELLENT"

    def test_good(self):
        assert get_health_status(79) == "GOOD"
        assert get_health_status(60) == "GOOD"

    def test_fair(self):
        assert get_health_status(59) == "FAIR"
        assert get_health_status(40) == "FAIR"

    def test_poor(self):
        assert get_health_status(39) == "POOR"
        assert get_health_status(20) == "POOR"

    def test_critical(self):
        assert get_health_status(19) == "CRITICAL"
        assert get_health_status(0) == "CRITICAL"


class TestGetHungerStatus:
    def test_satisfied(self):
        assert get_hunger_status(0) == "SATISFIED"
        assert get_hunger_status(20) == "SATISFIED"

    def test_peckish(self):
        assert get_hunger_status(21) == "PECKISH"
        assert get_hunger_status(40) == "PECKISH"

    def test_hungry(self):
        assert get_hunger_status(41) == "HUNGRY"
        assert get_hunger_status(60) == "HUNGRY"

    def test_starving(self):
        assert get_hunger_status(61) == "STARVING"
        assert get_hunger_status(80) == "STARVING"

    def test_desperate(self):
        assert get_hunger_status(81) == "DESPERATE"
        assert get_hunger_status(100) == "DESPERATE"


class TestGetHealthColor:
    def test_green_when_healthy(self):
        assert get_health_color(71) == COLOR_GREEN

    def test_yellow_when_moderate(self):
        assert get_health_color(50) == COLOR_YELLOW

    def test_red_when_critical(self):
        assert get_health_color(30) == COLOR_RED
