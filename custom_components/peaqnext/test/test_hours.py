"""Pure-function tests for service/hours.py (15-minute interval engine)."""
from datetime import timedelta

import pytest

from custom_components.peaqnext.service import hours
from custom_components.peaqnext.service.hours import (
    _blocked_interval,
    _create_prices_dict,
    _get_interval_index,
    _list_all_intervals,
    _set_dt_start_end,
    _update_comparers,
    cheapest_interval,
    get_intervals_sorted,
)
from custom_components.peaqnext.service.models.period_model import PeriodModel
from custom_components.peaqnext.test.conftest import TODAY, at


def flat(value=1.0, n=96):
    return [value] * n


# --- interval index -----------------------------------------------------


@pytest.mark.parametrize(
    "hour,minute,expected",
    [(0, 0, 0), (0, 14, 0), (0, 15, 1), (1, 0, 4), (12, 30, 50), (23, 59, 95)],
)
def test_interval_index(hour, minute, expected):
    assert _get_interval_index(at(hour, minute)) == expected


# --- prices dict --------------------------------------------------------


def test_prices_dict_drops_past_intervals():
    d = _create_prices_dict(([0, 1, 2, 3], []), current_interval=2)
    assert d == {2: 2, 3: 3}


def test_prices_dict_offsets_tomorrow_by_96():
    d = _create_prices_dict(([5], [7, 8]), current_interval=0)
    assert d == {0: 5, 96: 7, 97: 8}


# --- weighted sequences -------------------------------------------------


def test_list_all_intervals_flat_pattern_is_price_times_weight():
    seq = _list_all_intervals(([1.0, 2.0, 3.0], []), [2], 0)
    assert seq == {0: 2.0, 1: 4.0, 2: 6.0}


def test_list_all_intervals_multi_slot_pattern_sums_following_intervals():
    seq = _list_all_intervals(([1.0, 2.0, 3.0, 4.0], []), [1, 1], 0)
    assert seq == {0: 3.0, 1: 5.0, 2: 7.0}


def test_list_all_intervals_stops_when_pattern_does_not_fit():
    seq = _list_all_intervals(([1.0, 2.0], []), [1, 1, 1], 0)
    assert seq == {}


def test_list_all_intervals_bridges_midnight_with_tomorrow():
    prices = ([0.0] * 95 + [1.0], [2.0])
    seq = _list_all_intervals(prices, [1, 1], 95)
    assert seq == {95: 3.0}


# --- start / end datetimes ---------------------------------------------


def test_start_time_calculation_by_minute():
    start, end = _set_dt_start_end(
        at(10, 7), 3600, update_per_minute=True, interval_idx=42, calculate_end=False
    )
    # interval 42 is 10:30, now is interval 40 (10:00) => +30 min offset from 10:07
    assert start == at(10, 37)
    assert end == at(11, 37)


def test_start_time_rounds_down_to_interval_when_not_by_minute():
    start, end = _set_dt_start_end(
        at(10, 7), 3600, update_per_minute=False, interval_idx=42, calculate_end=False
    )
    assert start == at(10, 30)
    assert end == at(11, 30)


def test_end_time_calculation():
    start, end = _set_dt_start_end(
        at(10, 0), 3600, update_per_minute=False, interval_idx=44, calculate_end=True
    )
    assert end == at(12, 0)
    assert start == at(11, 0)
    assert end - start == timedelta(hours=1)


# --- blocked intervals --------------------------------------------------


def test_blocked_by_start():
    assert _blocked_interval(10, 14, [10], [])


def test_blocked_by_end():
    assert _blocked_interval(10, 14, [], [14])


def test_not_blocked_when_neither_matches():
    assert not _blocked_interval(10, 14, [11], [15])


def test_blocked_wraps_next_day_start():
    assert _blocked_interval(96 + 10, 96 + 14, [10], [])


def test_blocked_wraps_next_day_end():
    assert _blocked_interval(96 + 10, 96 + 14, [], [14])


# --- comparer normalisation --------------------------------------------


def test_comparers_unchanged_when_all_positive():
    periods = [PeriodModel(idx=i, price=p, sum_consumption_pattern=1) for i, p in enumerate([1, 2])]
    before = [p.comparer for p in periods]
    _update_comparers(periods)
    assert [p.comparer for p in periods] == before


def test_comparers_shifted_when_negative_prices_exist():
    periods = [PeriodModel(idx=i, price=p, sum_consumption_pattern=1) for i, p in enumerate([-1, 2])]
    _update_comparers(periods)
    assert all(p.comparer > 0 for p in periods)
    assert periods[0].comparer < periods[1].comparer


def test_update_comparers_empty_list_is_noop():
    _update_comparers([])


# --- get_intervals_sorted ----------------------------------------------


def _sorted(prices, pattern=(1,), **kw):
    args = dict(
        prices=prices,
        consumption_pattern=list(pattern),
        non_intervals_start=[],
        non_intervals_end=[],
        duration_in_seconds=3600,
        update_per_minute=False,
        calculate_end=False,
        mock_dt=at(0, 0),
    )
    args.update(kw)
    return get_intervals_sorted(**args)


def test_sorted_orders_by_price_ascending():
    prices = flat(1.0)
    prices[20] = 0.1
    result = _sorted((prices, []))
    assert result[0].idx == 20
    assert result[0].dt_start == at(5, 0)
    assert [p.comparer for p in result] == sorted(p.comparer for p in result)


def test_sorted_ties_broken_by_earliest_start():
    result = _sorted((flat(1.0), []))
    assert result[0].idx == 0
    assert result[1].idx == 1


def test_sorted_excludes_past_intervals():
    result = _sorted((flat(1.0), []), mock_dt=at(12, 0))
    assert min(p.idx for p in result) == 48


def test_sorted_includes_tomorrow_as_dates_after_today():
    prices = flat(1.0)
    result = _sorted((prices, flat(0.1, 4)), mock_dt=at(23, 0))
    cheapest = result[0]
    assert cheapest.dt_start.date() == TODAY + timedelta(days=1)


def test_sorted_respects_non_start_intervals():
    prices = flat(1.0)
    prices[20] = 0.1
    result = _sorted((prices, []), non_intervals_start=[20])
    assert 20 not in [p.idx for p in result]


def test_sorted_respects_non_end_intervals():
    prices = flat(1.0)
    prices[20] = 0.1
    # a 1h job starting at interval 20 ends at interval 24
    result = _sorted((prices, []), non_intervals_end=[24])
    assert 20 not in [p.idx for p in result]


def test_sorted_use_cent_converts_prices():
    result = _sorted(([100.0] * 96, []), use_cent=True)
    assert result[0].price == 1.0


def test_sorted_deficit_of_prices_returns_empty():
    assert _sorted(([], [])) == []


def test_sorted_returns_empty_list_on_error():
    # un-iterable prices must be swallowed and logged, never raised
    assert _sorted((None, None)) == []


def test_sorted_eur_currency_uses_higher_precision():
    result = _sorted(([0.123456] * 96, []), currency="EUR")
    assert result[0].comparer_addition is True


# --- cheapest_interval --------------------------------------------------


def _periods(*starts_and_prices):
    return [
        PeriodModel(
            idx=i,
            price=price,
            dt_start=start,
            dt_end=start + timedelta(hours=1),
            sum_consumption_pattern=1,
        )
        for i, (start, price) in enumerate(starts_and_prices)
    ]


def test_cheapest_empty_returns_invalid_model():
    result = cheapest_interval([])
    assert result.is_valid is False


def test_cheapest_returns_first_within_cap():
    items = _periods((at(1), 0.5), (at(2), 0.6), (at(20), 0.1))
    result = cheapest_interval(items, cheapest_cap=6, mock_dt=at(0))
    assert result.dt_start == at(1)


def test_cheapest_without_cap_uses_48h_horizon():
    items = _periods((at(20), 0.1))
    assert cheapest_interval(items, cheapest_cap=None, mock_dt=at(0)).is_valid


def test_cheapest_nothing_in_cap_returns_invalid_model():
    items = _periods((at(20), 0.1))
    assert cheapest_interval(items, cheapest_cap=2, mock_dt=at(0)).is_valid is False


def test_cheapest_override_end_filters_late_periods():
    items = _periods((at(1), 0.5), (at(5), 0.1))
    result = cheapest_interval(
        items, cheapest_cap=None, override_end=at(3), mock_dt=at(0)
    )
    assert result.dt_start == at(1)


def test_module_constants_are_consistent():
    assert hours.INTERVALS_PER_HOUR * hours.MINUTES_PER_INTERVAL == 60
