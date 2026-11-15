"""PeaqNextSensor entity, integration setup helpers and service handlers."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.peaqnext import async_create_internal_sensors
from custom_components.peaqnext.const import (
    CONF_CALCULATE_BY,
    CONF_CLOSEST_CHEAP,
    CONF_CONSUMPTION_TYPE,
    CONF_NAME,
    CONF_NONHOURS_END,
    CONF_NONHOURS_START,
    CONF_SENSORS,
    CONF_TOTAL_CONSUMPTION_IN_KWH,
    CONF_TOTAL_DURATION_IN_MINUTES,
    CONF_UPDATE_BY,
    DOMAIN,
)
from custom_components.peaqnext.sensors.next_sensor import PeaqNextSensor
from custom_components.peaqnext.service.models.consumption_type import ConsumptionType
from custom_components.peaqnext.service.models.next_sensor.enums.calculate_by import CalculateBy
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy
from custom_components.peaqnext.service.models.period_model import PeriodModel
from custom_components.peaqnext.services import (
    ServiceCalls,
    async_prepare_register_services,
)
from custom_components.peaqnext.test.conftest import at
from custom_components.peaqnext.test.test_hub import make_sensor


def make_entity(currency="SEK", use_cent=False):
    hub = MagicMock()
    hub.hub_id = 33512
    hub.hubname = "PeaqNext"
    hub.spotprice.currency = currency
    hub.spotprice.use_cent = use_cent
    return PeaqNextSensor(hub, "entry1", "Washing Machine")


# --- device_info (regression: sw_version must be a string) --------------


def test_device_info_values_are_strings_or_expected_types():
    info = make_entity().device_info
    for key in ("name", "sw_version", "model", "manufacturer"):
        assert isinstance(info[key], str), f"{key} must be str for the HA device registry"
    assert info["sw_version"] == "1"
    assert info["identifiers"] == {(DOMAIN, 33512)}


def test_unique_id_is_stable_and_scoped():
    e = make_entity()
    assert e.unique_id.startswith(f"{DOMAIN}_entry1_")
    assert e.unique_id == make_entity().unique_id


# --- currency formatting -----------------------------------------------


@pytest.mark.parametrize(
    "currency,cent,expected",
    [
        ("EUR", False, "€ 1.5"),
        ("EUR", True, "1.5¢"),
        ("SEK", False, "1.5 kr"),
        ("SEK", True, "1.5 öre"),
        ("NOK", False, "1.5 kr"),
        ("DKK", True, "1.5 øre"),
        ("GBP", False, "1.5 GBP"),
    ],
)
def test_currency_translation(currency, cent, expected):
    assert make_entity(currency, cent).currency_translation(1.5) == expected


def test_currency_translation_none_value():
    assert make_entity("SEK").currency_translation(None) == "- kr"


# --- display strings ----------------------------------------------------


def _period(start, end, price=1.0):
    return PeriodModel(idx=0, price=price, dt_start=start, dt_end=end, sum_consumption_pattern=1)


def _today(hour, minute=0):
    return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


def test_invalid_period_renders_empty_string():
    e = make_entity()
    assert e._make_string(PeriodModel(idx=0, price=0, is_valid=False)) == ""
    assert e._make_string(None) == ""


def test_absolute_display_has_minute_precision():
    e = make_entity()
    # the entity compares against the wall clock, so build periods on "today"
    p = _period(_today(5, 15), _today(6, 15))
    text = e._make_hours_display(p)
    assert "05:15-06:15" in text


def test_set_raw_start_format():
    assert PeaqNextSensor._set_raw_start(at(5, 15)) == "2023-07-30T05:15:00.000000"


# --- async_update copes with a failing hub -----------------------------


async def test_async_update_swallows_hub_errors():
    e = make_entity()
    e.hub.async_get_updates = AsyncMock(side_effect=RuntimeError("down"))
    await e.async_update()
    assert e.state is None


async def test_async_update_populates_state_from_hub():
    e = make_entity()
    period = _period(_today(5), _today(6), 0.5)
    e.hub.async_get_updates = AsyncMock(
        return_value={
            "best_close_start": period,
            "all_sequences": [period],
            "consumption_type": "flat",
            "duration_in_minutes": 60,
            "consumption_in_kwh": 1,
            "price_source": "nordpool",
            "update_by": UpdateBy.MINUTE,
            "calculate_by": CalculateBy.STARTTIME,
        }
    )
    await e.async_update()
    assert "05:00-06:00" in e.state
    assert e.extra_state_attributes["price_source"] == "Nordpool"
    assert e.extra_state_attributes["raw_start"].startswith(_today(5).strftime("%Y-%m-%dT05:00"))


# --- building sensors from config --------------------------------------


async def test_create_internal_sensors_maps_config():
    conf = SimpleNamespace(
        data={
            CONF_SENSORS: [
                {
                    CONF_NAME: "Dryer",
                    CONF_CONSUMPTION_TYPE: ConsumptionType.PeakIn.value,
                    CONF_TOTAL_DURATION_IN_MINUTES: 90,
                    CONF_TOTAL_CONSUMPTION_IN_KWH: 2.5,
                    CONF_NONHOURS_START: [1, 2],
                    CONF_NONHOURS_END: [3],
                    CONF_CLOSEST_CHEAP: 6,
                    CONF_UPDATE_BY: UpdateBy.HOUR.value,
                    CONF_CALCULATE_BY: CalculateBy.ENDTIME.value,
                },
                {
                    CONF_NAME: "Washer",
                    CONF_CONSUMPTION_TYPE: ConsumptionType.Flat.value,
                    CONF_TOTAL_DURATION_IN_MINUTES: 60,
                    CONF_TOTAL_CONSUMPTION_IN_KWH: 1,
                },
            ]
        }
    )
    dryer, washer = await async_create_internal_sensors(conf)
    assert dryer.consumption_type == ConsumptionType.PeakIn
    assert dryer.total_duration_in_minutes == 90
    assert dryer.non_hours_start == [1, 2]
    assert dryer.non_hours_end == [3]
    assert dryer.default_closest_cheap == 6
    assert dryer.update_by == UpdateBy.HOUR
    assert dryer.calculate_by == CalculateBy.ENDTIME
    # defaults
    assert washer.default_closest_cheap == 12
    assert washer.calculate_by == CalculateBy.STARTTIME
    assert washer.non_hours_start == []


# --- services -----------------------------------------------------------


@pytest.fixture
async def registered():
    hub = MagicMock()
    sensor = make_sensor("washer")
    sensor.async_override_sensor_data = AsyncMock()
    sensor.async_cancel_override = AsyncMock()
    hub.sensors_dict = {"washer": sensor}
    hass = MagicMock()
    await async_prepare_register_services(hub, hass)
    handlers = {c.args[1]: c.args[2] for c in hass.services.async_register.call_args_list}
    return sensor, handlers


async def test_both_services_are_registered(registered):
    _, handlers = registered
    assert set(handlers) == {s.value for s in ServiceCalls}


@pytest.mark.parametrize("entity_id", ["sensor.peaqnext_washer", "sensor.washer", "WASHER"])
async def test_override_service_resolves_entity_ids(registered, entity_id):
    sensor, handlers = registered
    call = SimpleNamespace(
        data={"sensor_entity": entity_id, "consumption_in_kwh": 5, "duration_in_minutes": 30}
    )
    await handlers[ServiceCalls.OVERRIDE_SENSOR_DATA.value](call)
    sensor.async_override_sensor_data.assert_awaited_once()
    kwargs = sensor.async_override_sensor_data.call_args.kwargs
    assert kwargs["total_consumption_in_kwh"] == 5
    assert kwargs["total_duration_in_minutes"] == 30
    assert kwargs["timeout"] is None


async def test_override_service_unknown_sensor_is_logged_not_raised(registered):
    sensor, handlers = registered
    call = SimpleNamespace(data={"sensor_entity": "sensor.peaqnext_unknown"})
    await handlers[ServiceCalls.OVERRIDE_SENSOR_DATA.value](call)
    sensor.async_override_sensor_data.assert_not_awaited()


async def test_cancel_service_calls_sensor(registered):
    sensor, handlers = registered
    call = SimpleNamespace(data={"sensor_entity": "sensor.peaqnext_washer"})
    await handlers[ServiceCalls.CANCEL_OVERRIDE.value](call)
    sensor.async_cancel_override.assert_awaited_once()
