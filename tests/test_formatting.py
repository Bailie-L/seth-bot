"""Tests for utils/formatting.py"""
from utils.formatting import SethVisuals


class TestHealthBar:
    def test_full_health(self):
        result = SethVisuals.health_bar(100, 100)
        assert "██████████" in result
        assert "100%" in result

    def test_zero_health(self):
        result = SethVisuals.health_bar(0, 100)
        assert "░░░░░░░░░░" in result
        assert "0%" in result

    def test_half_health(self):
        result = SethVisuals.health_bar(50, 100)
        assert "█████░░░░░" in result
        assert "50%" in result

    def test_critical_health(self):
        result = SethVisuals.health_bar(15, 100)
        assert "█░░░░░░░░░" in result

    def test_excellent_health(self):
        result = SethVisuals.health_bar(85, 100)
        assert "████████░░" in result


class TestHungerBar:
    def test_no_hunger(self):
        result = SethVisuals.hunger_bar(0)
        assert "██████████" in result
        assert "100% full" in result
        assert "Hunger: 0" in result

    def test_max_hunger(self):
        result = SethVisuals.hunger_bar(100)
        assert "░░░░░░░░░░" in result
        assert "0% full" in result

    def test_half_hunger(self):
        result = SethVisuals.hunger_bar(50)
        assert "█████░░░░░" in result
        assert "50% full" in result


class TestResourceBar:
    def test_full_resource(self):
        result = SethVisuals.resource_bar(10, 10)
        assert "██████████" in result
        assert "100%" in result

    def test_with_fraction(self):
        result = SethVisuals.resource_bar(3, 10, show_fraction=True)
        assert "3/10" in result

    def test_zero_max(self):
        result = SethVisuals.resource_bar(0, 0)
        assert "0%" in result
