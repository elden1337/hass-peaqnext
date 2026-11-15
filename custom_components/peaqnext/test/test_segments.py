import pytest

from custom_components.peaqnext.service.models.consumption_type import ConsumptionType
from custom_components.peaqnext.service.segments import (
    calculate_consumption_per_hour,
)


BUG_FIRST_HOUR = pytest.mark.xfail(
    strict=True,
    reason="segments.py flushes the hour bucket AFTER adding minute t%60==0, "
    "so the first bucket contains 61 minutes (e.g. 10 kWh/120 min -> [5.1, 4.9]).",
)


def calc(kwh, minutes, ctype, custom=None, start_minute=0):
    return calculate_consumption_per_hour(
        kwh, minutes * 60, ctype, custom or [], start_minute
    )


def test_flat_one_hour_is_total_consumption():
    assert calc(10, 60, ConsumptionType.Flat) == [10]


@BUG_FIRST_HOUR
def test_flat_two_hours_splits_evenly():
    assert calc(10, 120, ConsumptionType.Flat) == [5, 5]


def test_total_consumption_is_preserved_for_all_builtin_types():
    for ctype in (
        ConsumptionType.Flat,
        ConsumptionType.PeakIn,
        ConsumptionType.PeakOut,
        ConsumptionType.MidPeak,
        ConsumptionType.PeakInOut,
    ):
        assert sum(calc(12, 240, ctype)) == pytest.approx(12, abs=0.2), ctype


def test_peak_in_front_loads_consumption():
    result = calc(10, 240, ConsumptionType.PeakIn)
    assert result[0] > result[-1]


def test_peak_out_back_loads_consumption():
    result = calc(10, 240, ConsumptionType.PeakOut)
    assert result[-1] > result[0]


@BUG_FIRST_HOUR
def test_peak_in_out_is_symmetric():
    result = calc(10, 240, ConsumptionType.PeakInOut)
    assert result[0] == result[-1]
    assert result[0] > result[1]


@BUG_FIRST_HOUR
def test_custom_pattern_is_proportional():
    result = calc(10, 120, ConsumptionType.Custom, custom=[1, 3])
    assert result == [2.5, 7.5]


def test_start_minute_shifts_hour_boundaries():
    # starting at :30, a 60min job spans two clock hours
    result = calc(10, 60, ConsumptionType.Flat, start_minute=30)
    assert len(result) == 2
    assert sum(result) == pytest.approx(10, abs=0.2)


def test_invalid_custom_pattern_falls_back_to_total():
    # empty custom pattern cannot be segmented; documented fallback is [total]
    assert calc(10, 60, ConsumptionType.Custom, custom=[]) == [10]
