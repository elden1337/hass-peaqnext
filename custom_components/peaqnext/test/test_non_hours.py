"""Non-hours are configured as clock hours (0-23) in the config flow.

These tests drive a full NextSensor with a fixed clock and 96 quarter-hour prices.
"""
import pytest

from custom_components.peaqnext.service.models.consumption_type import ConsumptionType
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy
from custom_components.peaqnext.service.models.sensor_model import NextSensor
from custom_components.peaqnext.test.conftest import TODAY

HOURS_VS_INTERVALS_BUG = pytest.mark.xfail(
    strict=True,
    reason="config_flow offers non-hours as clock hours 0-23, but hours._blocked_interval "
    "compares them with 15-minute interval indices 0-95 (hour 6 blocks 01:30, not 06:00).",
)


def sensor(**kw):
    s = NextSensor(
        consumption_type=ConsumptionType.Flat,
        name="t",
        hass_entity_id="sensor.t",
        total_duration_in_minutes=60,
        total_consumption_in_kwh=1,
        update_by=UpdateBy.HOUR,
        **kw,
    )
    s.dt_model.set_date(TODAY)
    s.dt_model.set_hour(0)
    s.dt_model.set_minute(0)
    return s


PRICES = ([1.0] * 96, [])


async def test_no_non_hours_keeps_every_candidate():
    s = sensor()
    await s.async_update_sensor(PRICES)
    hours = {p.dt_start.hour for p in s.all_sequences}
    assert {1, 6, 12, 20} <= hours


@HOURS_VS_INTERVALS_BUG
async def test_non_hours_start_blocks_that_clock_hour():
    s = sensor(non_hours_start=[6])
    await s.async_update_sensor(PRICES)
    assert all(p.dt_start.hour != 6 for p in s.all_sequences)
    # ...and must not over-block: other hours stay available
    assert any(p.dt_start.hour == 1 for p in s.all_sequences)


@HOURS_VS_INTERVALS_BUG
async def test_non_hours_end_blocks_that_clock_hour():
    s = sensor(non_hours_end=[6])
    await s.async_update_sensor(PRICES)
    assert all(p.dt_end.hour != 6 for p in s.all_sequences)
    assert any(p.dt_end.hour == 2 for p in s.all_sequences)


@pytest.mark.xfail(
    strict=True,
    reason="segments.py yields one slot per CLOCK HOUR but hours.py maps each slot to a "
    "15-minute interval, so a 60-minute job is priced from only its first quarter-hour.",
)
async def test_job_price_accounts_for_every_quarter_it_runs_through():
    prices = [1.0] * 96
    prices[10] = 100.0  # expensive quarter 02:30-02:45
    s = sensor()
    await s.async_update_sensor((prices, []))
    by_idx = {p.idx: p for p in s.all_sequences}
    # a 1h job starting at 01:30 (idx 6) runs through idx 6..9; starting at 02:00 (idx 8)
    # runs through 8..11 and therefore includes the expensive quarter
    assert by_idx[8].price > by_idx[4].price
