from custom_components.peaqnext.service.models.hour_model import HourModel
from datetime import datetime, timedelta, date
import logging

_LOGGER = logging.getLogger(__name__)

MAX_TIME_DIFF = 48

def get_hours_sorted(
    prices: tuple[list,list],
    consumption_pattern: list[float],
    non_hours_start: list[int],
    non_hours_end: list[int],
    duration_in_seconds: int,
    update_per_minute: bool,
    calculate_end: bool,
    mock_dt: datetime|None = None,
    use_cent: bool = False,
    currency: str = "sek"
    
) -> list[HourModel]:
    _start = _get_datetime(mock_dt)
    try:
        sequences = _list_all_hours(prices, consumption_pattern, mock_dt.hour)
        ret = [] 
        for s in sequences:
            _dt_start, _dt_end = _set_dt_start_end(_start, duration_in_seconds, update_per_minute, s, calculate_end)
            if _blocked_hour(s, _dt_end.hour, non_hours_start, non_hours_end):
                continue
            ret.append(HourModel(
                dt_start=_dt_start,
                dt_end = _dt_end,
                idx=s,
                price=sequences[s],
                use_cent=use_cent,
                sum_consumption_pattern=sum(consumption_pattern),
                comparer_addition = currency.lower() == "eur"
            ))
        _update_comparers(ret)
        return list(sorted(ret, key=lambda i: (i.comparer, i.dt_start)))
    except Exception as e:
        _LOGGER.exception(e)
        return []


def cheapest_hour(
    hours_list: list[HourModel], cheapest_cap: int|None = None, override_end: datetime|None = None, mock_dt: datetime = None
) -> HourModel:
    if len(hours_list) == 0:
        return HourModel(idx=0, price=0, is_valid=False)
    _now = _get_datetime(mock_dt)
    hour_limit = _now + timedelta(hours=cheapest_cap) if cheapest_cap is not None else _now + timedelta(hours=MAX_TIME_DIFF)
    ret = [v for v in hours_list if v.dt_start < hour_limit and (override_end is None or v.dt_end < override_end)]
    try:
        return ret[0]
    except Exception as e:
        _LOGGER.error(f"Unable to get cheapest hour. Exception: {e}. Data: hour_limit:{hour_limit}, available hours:{[h.dt_start.strftime('%d, %H:%M') for h in hours_list]}")
        return HourModel(idx=0, price=0, is_valid=False)


def _list_all_hours(prices: list, consumption_pattern: list, hour: int) -> dict:
    sequences = {}
    prices_dict = _create_prices_dict(prices, hour)
    for p in prices_dict:
        try:
            if p + len(consumption_pattern) - 1 > max(prices_dict.keys()):
                break
            internal_sum = sum(prices_dict[p + i] * consumption_pattern[i] for i in range(len(consumption_pattern)))
            sequences[p] = round(internal_sum, 2)
        except Exception as e:
            _LOGGER.exception("Error in _list_all_hours: %s", e)
            continue
    return sequences


def _set_dt_start_end(_start: datetime, duration_in_seconds: int, update_per_minute: bool, s: int, calculate_end: bool) -> tuple[datetime, datetime]:
    _dt_start: datetime
    _dt_end: datetime
    if not calculate_end:
        _dt_start = _start +timedelta(hours=s - _start.hour)
        if not update_per_minute:
            _dt_start = _dt_start.replace(minute=0)
        _dt_end = _dt_start + timedelta(seconds=duration_in_seconds)
    else:
        _dt_end = (_start +timedelta(hours=s - _start.hour) + timedelta(seconds=duration_in_seconds)).replace(minute=_start.minute * int(update_per_minute))
        _dt_start = _dt_end - timedelta(seconds=duration_in_seconds)
    return (_dt_start, _dt_end)


def _create_prices_dict(prices: tuple[list,list], hour: int) -> dict[int, float]:
    prices_dict = {k: v for k, v in enumerate(prices[0]) if k >= hour}
    prices_dict.update({k + 24: v for k, v in enumerate(prices[1])})
    return prices_dict


def _update_comparers(ret: list[HourModel]) -> None:
    comparers = [h.comparer for h in ret]
    min_val = min(comparers) if comparers else 1
    if min_val <= 0:
        for r in ret:
            r.comparer += abs(min_val) + 0.01


def _blocked_hour(idx: int, end_hour:int,  non_hours_start: list[int], non_hours_end: list[int]) -> bool:
    return any([
            end_hour in non_hours_end,
            end_hour - 24 in non_hours_end,
            idx in non_hours_start,
            idx - 24 in non_hours_start,
        ])


def _get_datetime(mock_dt: datetime = None) -> datetime:
    return mock_dt if mock_dt is not None else datetime.now()


