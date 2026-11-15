import pytest
import voluptuous as vol

from custom_components.peaqnext.config_flow import SENSORS_SCHEMA, ConfigFlow
from custom_components.peaqnext.const import (
    CONF_CLOSEST_CHEAP,
    CONF_CONSUMPTION_TYPE,
    CONF_NAME,
    CONF_SENSORS,
    CONF_TOTAL_CONSUMPTION_IN_KWH,
    CONF_TOTAL_DURATION_IN_MINUTES,
    CONF_UPDATE_BY,
)
from custom_components.peaqnext.service.models.consumption_type import (
    CONSUMPTIONTYPE_NAMES,
)
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy

VALID = {
    CONF_NAME: "washer",
    CONF_CONSUMPTION_TYPE: CONSUMPTIONTYPE_NAMES[0],
    CONF_TOTAL_CONSUMPTION_IN_KWH: 1.5,
    CONF_TOTAL_DURATION_IN_MINUTES: 90,
}


# --- schema --------------------------------------------------------------


def test_schema_applies_defaults():
    out = SENSORS_SCHEMA(dict(VALID))
    assert out[CONF_CLOSEST_CHEAP] == 12
    assert out["deduct_price"] == 0
    assert out["show_relative_time"] is False
    assert out[CONF_UPDATE_BY] == UpdateBy.MINUTE.value


@pytest.mark.parametrize("missing", [CONF_NAME, CONF_CONSUMPTION_TYPE,
                                     CONF_TOTAL_CONSUMPTION_IN_KWH,
                                     CONF_TOTAL_DURATION_IN_MINUTES])
def test_schema_requires_core_fields(missing):
    data = dict(VALID)
    del data[missing]
    with pytest.raises(vol.Invalid):
        SENSORS_SCHEMA(data)


def test_schema_rejects_unknown_consumption_type():
    with pytest.raises(vol.Invalid):
        SENSORS_SCHEMA({**VALID, CONF_CONSUMPTION_TYPE: "does-not-exist"})


def test_schema_rejects_negative_consumption():
    with pytest.raises(vol.Invalid):
        SENSORS_SCHEMA({**VALID, CONF_TOTAL_CONSUMPTION_IN_KWH: -1})


def test_schema_rejects_hours_out_of_range():
    with pytest.raises(vol.Invalid):
        SENSORS_SCHEMA({**VALID, "non_hours_start": [24]})


def test_schema_accepts_valid_non_hours():
    out = SENSORS_SCHEMA({**VALID, "non_hours_start": [1, 2], "non_hours_end": [23]})
    assert out["non_hours_start"] == [1, 2]


# --- flow ---------------------------------------------------------------


def _flow():
    flow = ConfigFlow()
    flow.hass = None
    flow.context = {}
    flow.handler = "peaqnext"
    flow.flow_id = "test"
    return flow


async def test_first_step_shows_form():
    result = await _flow().async_step_user()
    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_single_sensor_creates_entry():
    flow = _flow()
    await flow.async_step_user()
    result = await flow.async_step_user(dict(VALID))
    assert result["type"] == "create_entry"
    sensors = result["data"][CONF_SENSORS]
    assert len(sensors) == 1
    assert sensors[0][CONF_NAME] == "washer"
    assert sensors[0][CONF_TOTAL_DURATION_IN_MINUTES] == 90


async def test_add_another_sensor_loops_back_to_form():
    flow = _flow()
    await flow.async_step_user()
    result = await flow.async_step_user({**VALID, "add_another_sensor": True})
    assert result["type"] == "form"
    result = await flow.async_step_user({**VALID, CONF_NAME: "dryer"})
    assert result["type"] == "create_entry"
    assert [s[CONF_NAME] for s in result["data"][CONF_SENSORS]] == ["washer", "dryer"]


async def test_entry_defaults_for_optional_fields():
    flow = _flow()
    await flow.async_step_user()
    result = await flow.async_step_user(dict(VALID))
    sensor = result["data"][CONF_SENSORS][0]
    assert sensor[CONF_CLOSEST_CHEAP] == 12
    assert sensor["non_hours_start"] == []
    assert sensor["non_hours_end"] == []
