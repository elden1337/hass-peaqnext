"""Shared fixtures and helpers for the peaqnext test-suite."""
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.peaqnext.service.hub import Hub

# A fixed "today" so tests never depend on the wall clock.
TODAY = date(2023, 7, 30)


def at(hour: int, minute: int = 0, day: date = TODAY) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute)


def fake_state(
    state="0.5",
    today=None,
    tomorrow=None,
    tomorrow_valid=False,
    currency="SEK",
    **extra,
):
    """Minimal stand-in for a HA State object."""
    attributes = {
        "today": [0.1] * 96 if today is None else today,
        "tomorrow": [] if tomorrow is None else tomorrow,
        "tomorrow_valid": tomorrow_valid,
        "currency": currency,
        **extra,
    }
    return SimpleNamespace(state=state, attributes=attributes)


@pytest.fixture(autouse=True)
def reset_hub_class_state():
    """Hub keeps sensors in class-level containers; isolate every test."""
    Hub.sensors = []
    Hub.sensors_dict = {}
    yield
    Hub.sensors = []
    Hub.sensors_dict = {}


@pytest.fixture
def fake_hub():
    hub = MagicMock()
    hub.async_update_prices = AsyncMock()
    hub.state_machine = MagicMock()
    return hub
