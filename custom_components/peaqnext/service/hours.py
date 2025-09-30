from custom_components.peaqnext.service.models.period_model import PeriodModel
from datetime import datetime, timedelta, date
import logging

_LOGGER = logging.getLogger(__name__)

MAX_TIME_DIFF = 48  # hours
MINUTES_PER_INTERVAL = 15
INTERVALS_PER_HOUR = 60 // MINUTES_PER_INTERVAL  # 4 intervals per hour


def get_intervals_sorted(
        prices: tuple[list, list],
        consumption_pattern: list[float],
        non_intervals_start: list[int],
        non_intervals_end: list[int],
        duration_in_seconds: int,
        update_per_minute: bool,
        calculate_end: bool,
        mock_dt: datetime | None = None,
        use_cent: bool = False,
        currency: str = "sek"
) -> list[PeriodModel]:
    _start = _get_datetime(mock_dt)
    try:
        current_interval = _get_interval_index(_start)
        sequences = _list_all_intervals(prices, consumption_pattern, current_interval)
        ret = []

        for interval_idx in sequences:
            _dt_start, _dt_end = _set_dt_start_end(
                _start, duration_in_seconds, update_per_minute,
                interval_idx, calculate_end
            )
            end_interval_idx = _get_interval_index(_dt_end)

            if _blocked_interval(interval_idx, end_interval_idx, non_intervals_start, non_intervals_end):
                continue

            ret.append(PeriodModel(
                dt_start=_dt_start,
                dt_end=_dt_end,
                idx=interval_idx,
                price=sequences[interval_idx],
                use_cent=use_cent,
                sum_consumption_pattern=sum(consumption_pattern),
                comparer_addition=currency.lower() == "eur"
            ))

        _update_comparers(ret)
        return list(sorted(ret, key=lambda i: (i.comparer, i.dt_start)))
    except Exception as e:
        _LOGGER.exception(e)
        return []


def cheapest_interval(
        intervals_list: list[PeriodModel],
        cheapest_cap: int | None = None,
        override_end: datetime | None = None,
        mock_dt: datetime = None
) -> PeriodModel:
    if len(intervals_list) == 0:
        return PeriodModel(idx=0, price=0, is_valid=False)

    _now = _get_datetime(mock_dt)
    hour_limit = _now + timedelta(hours=cheapest_cap) if cheapest_cap is not None else _now + timedelta(
        hours=MAX_TIME_DIFF)
    ret = [v for v in intervals_list if v.dt_start < hour_limit and (override_end is None or v.dt_end < override_end)]

    try:
        return ret[0]
    except Exception as e:
        _LOGGER.error(
            f"Unable to get cheapest interval. Exception: {e}. "
            f"Data: hour_limit:{hour_limit}, "
            f"available intervals:{[h.dt_start.strftime('%d, %H:%M') for h in intervals_list]}"
        )
        return PeriodModel(idx=0, price=0, is_valid=False)


def _list_all_intervals(prices: tuple[list, list], consumption_pattern: list, current_interval: int) -> dict:
    sequences = {}
    prices_dict = _create_prices_dict(prices, current_interval)

    for interval_idx in prices_dict:
        try:
            # Check if we have enough intervals remaining for the full pattern
            if interval_idx + len(consumption_pattern) - 1 > max(prices_dict.keys()):
                break

            # Calculate weighted sum across all intervals in the consumption pattern
            internal_sum = sum(
                prices_dict[interval_idx + i] * consumption_pattern[i]
                for i in range(len(consumption_pattern))
            )
            sequences[interval_idx] = round(internal_sum, 2)
        except Exception as e:
            _LOGGER.exception("Error in _list_all_intervals: %s", e)
            continue

    return sequences


def _set_dt_start_end(
        _start: datetime,
        duration_in_seconds: int,
        update_per_minute: bool,
        interval_idx: int,
        calculate_end: bool
) -> tuple[datetime, datetime]:
    current_interval = _get_interval_index(_start)
    interval_diff = interval_idx - current_interval
    minutes_diff = interval_diff * MINUTES_PER_INTERVAL

    if not calculate_end:
        _dt_start = _start + timedelta(minutes=minutes_diff)
        if not update_per_minute:
            # Round down to the nearest 15-minute interval
            _dt_start = _dt_start.replace(minute=(_dt_start.minute // MINUTES_PER_INTERVAL) * MINUTES_PER_INTERVAL,
                                          second=0, microsecond=0)
        _dt_end = _dt_start + timedelta(seconds=duration_in_seconds)
    else:
        _dt_end = _start + timedelta(minutes=minutes_diff) + timedelta(seconds=duration_in_seconds)
        if update_per_minute:
            _dt_end = _dt_end.replace(minute=_start.minute)
        _dt_start = _dt_end - timedelta(seconds=duration_in_seconds)

    return (_dt_start, _dt_end)


def _create_prices_dict(prices: tuple[list, list], current_interval: int) -> dict[int, float]:
    # Today's prices starting from current interval
    prices_dict = {k: v for k, v in enumerate(prices[0]) if k >= current_interval}

    # Tomorrow's prices (offset by 96 intervals = 24 hours)
    prices_dict.update({k + 96: v for k, v in enumerate(prices[1])})

    return prices_dict


def _update_comparers(ret: list[PeriodModel]) -> None:
    comparers = [h.comparer for h in ret]
    min_val = min(comparers) if comparers else 1
    if min_val <= 0:
        for r in ret:
            r.comparer += abs(min_val) + 0.01


def _blocked_interval(
        idx: int,
        end_idx: int,
        non_intervals_start: list[int],
        non_intervals_end: list[int]
) -> bool:
    return any([
        end_idx in non_intervals_end,
        end_idx - 96 in non_intervals_end,  # Yesterday's equivalent interval
        idx in non_intervals_start,
        idx - 96 in non_intervals_start,  # Yesterday's equivalent interval
    ])


def _get_interval_index(dt: datetime) -> int:
    return (dt.hour * INTERVALS_PER_HOUR) + (dt.minute // MINUTES_PER_INTERVAL)


def _get_datetime(mock_dt: datetime = None) -> datetime:
    return mock_dt if mock_dt is not None else datetime.now()