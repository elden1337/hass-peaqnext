import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.peaqnext.service.hub import SPOTPRICE_UPDATE_FORCE, Hub
from custom_components.peaqnext.service.models.consumption_type import ConsumptionType
from custom_components.peaqnext.service.models.sensor_model import NextSensor
from custom_components.peaqnext.test.conftest import TODAY, fake_state


def make_sensor(name="washer", **kw):
    s = NextSensor(
        consumption_type=ConsumptionType.Flat,
        name=name,
        hass_entity_id=name,
        total_duration_in_minutes=60,
        total_consumption_in_kwh=1,
        **kw,
    )
    s.dt_model.set_date(TODAY)
    s.dt_model.set_hour(0)
    s.dt_model.set_minute(0)
    return s


@pytest.fixture
def hub():
    h = Hub(None, test=True)
    h.spotprice.state_machine = MagicMock()
    h.spotprice._entity = "sensor.np"
    return h


async def test_setup_registers_sensors_by_entity_id(hub):
    a, b = make_sensor("a"), make_sensor("b")
    await hub.async_setup([a, b])
    assert hub.sensors_dict == {"a": a, "b": b}


async def test_update_prices_updates_every_sensor(hub):
    a, b = make_sensor("a"), make_sensor("b")
    await hub.async_setup([a, b])
    await hub.async_update_prices(([1.0] * 96, []))
    assert a.all_sequences and b.all_sequences
    assert hub.prices == ([1.0] * 96, [])


async def test_update_prices_isolates_failing_sensor(hub):
    bad, good = make_sensor("bad"), make_sensor("good")
    bad.async_update_sensor = AsyncMock(side_effect=RuntimeError("boom"))
    await hub.async_setup([bad, good])
    await hub.async_update_prices(([1.0] * 96, []))
    assert good.all_sequences


async def test_get_updates_unknown_sensor_returns_empty_dict(hub):
    hub.latest_spotprice_update = time.time()
    assert await hub.async_get_updates("nope") == {}


async def test_get_updates_returns_expected_payload(hub):
    s = make_sensor("washer")
    await hub.async_setup([s])
    hub.latest_spotprice_update = time.time()
    await hub.async_update_prices(([1.0] * 96, []))
    status = await hub.async_get_updates("washer")
    assert set(status) == {
        "state", "best_close_start", "all_sequences", "consumption_type",
        "duration_in_minutes", "consumption_in_kwh", "non_hours_start",
        "non_hours_end", "closest_cheap_hour", "custom_consumption_pattern",
        "price_source", "update_by", "calculate_by", "relative_time",
    }
    assert status["duration_in_minutes"] == 60
    assert status["consumption_type"] == ConsumptionType.Flat.value
    assert status["price_source"] == "nordpool"


async def test_get_updates_forces_refresh_when_stale(hub):
    hub.spotprice.async_update_spotprice = AsyncMock()
    hub.latest_spotprice_update = time.time() - SPOTPRICE_UPDATE_FORCE - 1
    await hub.async_get_updates("nope")
    hub.spotprice.async_update_spotprice.assert_awaited_once()
    assert time.time() - hub.latest_spotprice_update < 5


async def test_get_updates_skips_refresh_when_fresh(hub):
    hub.spotprice.async_update_spotprice = AsyncMock()
    hub.latest_spotprice_update = time.time()
    await hub.async_get_updates("nope")
    hub.spotprice.async_update_spotprice.assert_not_awaited()


def _event(old, new, entity="sensor.np"):
    return MagicMock(data={"entity_id": entity, "old_state": old, "new_state": new})


async def test_state_change_triggers_price_refresh(hub):
    hub.spotprice.async_update_spotprice = AsyncMock()
    await hub._async_on_change(_event("a", "b"))
    hub.spotprice.async_update_spotprice.assert_awaited_once()


async def test_state_change_without_difference_is_ignored(hub):
    hub.spotprice.async_update_spotprice = AsyncMock()
    await hub._async_on_change(_event("a", "a"))
    hub.spotprice.async_update_spotprice.assert_not_awaited()


async def test_state_change_first_state_triggers_refresh(hub):
    hub.spotprice.async_update_spotprice = AsyncMock()
    await hub._async_on_change(_event(None, "a"))
    hub.spotprice.async_update_spotprice.assert_awaited_once()


async def test_state_change_error_is_swallowed(hub):
    hub.spotprice.async_update_spotprice = AsyncMock(side_effect=RuntimeError("x"))
    await hub._async_on_change(_event(None, "a"))


async def test_end_to_end_state_to_sensor(hub):
    """spot-price state -> updater -> hub -> sensor sequences."""
    s = make_sensor("washer")
    await hub.async_setup([s])
    prices = [1.0] * 96
    prices[40] = 0.1
    hub.spotprice.state_machine.states.get.return_value = fake_state(today=prices)
    await hub.spotprice.async_update_spotprice()
    assert s.all_sequences[0].idx == 40
