"""Tests for cogs/seth_core.py — pure helper methods"""
import discord
from cogs.seth_core import SethCore


class FakeBot:
    """Minimal stand-in for discord.Bot"""
    pass


class TestGetHealthStatus:
    def setup_method(self):
        self.core = SethCore(FakeBot())

    def test_excellent(self):
        assert self.core.get_health_status(100) == "EXCELLENT"
        assert self.core.get_health_status(80) == "EXCELLENT"

    def test_good(self):
        assert self.core.get_health_status(79) == "GOOD"
        assert self.core.get_health_status(60) == "GOOD"

    def test_fair(self):
        assert self.core.get_health_status(59) == "FAIR"
        assert self.core.get_health_status(40) == "FAIR"

    def test_poor(self):
        assert self.core.get_health_status(39) == "POOR"
        assert self.core.get_health_status(20) == "POOR"

    def test_critical(self):
        assert self.core.get_health_status(19) == "CRITICAL"
        assert self.core.get_health_status(0) == "CRITICAL"


class TestGetHungerStatus:
    def setup_method(self):
        self.core = SethCore(FakeBot())

    def test_satisfied(self):
        assert self.core.get_hunger_status(0) == "SATISFIED"
        assert self.core.get_hunger_status(20) == "SATISFIED"

    def test_peckish(self):
        assert self.core.get_hunger_status(21) == "PECKISH"
        assert self.core.get_hunger_status(40) == "PECKISH"

    def test_hungry(self):
        assert self.core.get_hunger_status(41) == "HUNGRY"
        assert self.core.get_hunger_status(60) == "HUNGRY"

    def test_starving(self):
        assert self.core.get_hunger_status(61) == "STARVING"
        assert self.core.get_hunger_status(80) == "STARVING"

    def test_desperate(self):
        assert self.core.get_hunger_status(81) == "DESPERATE"
        assert self.core.get_hunger_status(100) == "DESPERATE"


class TestGetHealthColor:
    def setup_method(self):
        self.core = SethCore(FakeBot())

    def test_green_when_healthy(self):
        assert self.core.get_health_color(71) == discord.Color.green()

    def test_yellow_when_moderate(self):
        assert self.core.get_health_color(50) == discord.Color.yellow()

    def test_red_when_critical(self):
        assert self.core.get_health_color(30) == discord.Color.red()
