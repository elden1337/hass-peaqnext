from custom_components.peaqnext.service.models.hour_model import HourModel
from datetime import datetime, timedelta, date
import logging

_LOGGER = logging.getLogger(__name__)

async def async_get_hours_sorted(
    prices: tuple[list,list],
    consumption_pattern: list[float],
    non_hours_start: list[int],
    non_hours_end: list[int],
    duration_in_seconds: int,
    mock_hour: int|None = None,
    mock_date: date|None = None,
    use_cent: bool = False
) -> list[HourModel]:
    _hour = datetime.now().hour if mock_hour is None else mock_hour
    sequences = await async_list_all_hours(create_prices_dict(prices, _hour), consumption_pattern)
    _start = _get_datetime(mock_hour, mock_date)
    ret = [] 
    for s in sequences:
        _dt_start = _start +timedelta(hours=s - _start.hour)
        _end = _dt_start + timedelta(seconds=duration_in_seconds)
        if _blocked_hour(s, _end.hour, non_hours_start, non_hours_end):
            continue
        ret.append(HourModel(
            dt_start=_dt_start,
            dt_end = _end,
            idx=s,
            price=sequences[s],
            use_cent=use_cent,
            sum_consumption_pattern=sum(consumption_pattern)
        ))
    return list(sorted(ret, key=lambda i: (i.comparer, i.dt_start)))


def _blocked_hour(idx: int, end_hour:int,  non_hours_start: list[int], non_hours_end: list[int]) -> bool:
    return any([
            end_hour in non_hours_end,
            end_hour - 24 in non_hours_end,
            idx in non_hours_start,
            idx - 24 in non_hours_start,
        ])

def create_prices_dict(prices: tuple[list,list], hour: int) -> dict[int, float]:
    prices_dict = {k: v for k, v in enumerate(prices[0]) if k >= hour}
    prices_dict.update({k + 24: v for k, v in enumerate(prices[1])})
    return prices_dict

def _get_datetime(mock_hour: int = None, mock_date: date = None) -> datetime:
    _date: date = datetime.now().date() if mock_date is None else mock_date
    _dt = datetime.combine(_date, datetime.now().time().replace(minute=0, second=0, microsecond=0))
    _now:datetime = _dt if mock_hour is None else _dt.replace(hour=mock_hour)
    return _now

def cheapest_hour(
    hours_list: list[HourModel], cheapest_cap: int|None = None, mock_hour: int = None, mock_date: date = None
) -> HourModel:
    _now = _get_datetime(mock_hour, mock_date)
    hour_limit = _now + timedelta(hours=cheapest_cap) if cheapest_cap is not None else _now + timedelta(hours=48)
    ret = [v for v in hours_list if v.dt_start < hour_limit]
    try:
        if cheapest_cap is None:
            print("hour_limit", hour_limit)
            print("now", _now)
            print("ret[0]", ret[0])
        return ret[0]
    except Exception as e:
        _LOGGER.error(f"Unable to get cheapest hour. Exception: {e}. Data: hour_limit:{hour_limit}, available hours:{[h.dt_start.strftime('%d, %H:%M') for h in hours_list]}")
        return HourModel(0, 0, 0, 0)


async def async_list_all_hours(
    prices_dict: dict,
    consumption_pattern: list,
) -> dict:
    sequences = {}
    for p in prices_dict:
        try:
            if p + len(consumption_pattern) - 1 > max([h for h in prices_dict.keys()]):
                break
            internal_sum = 0
            for i in range(0, len(consumption_pattern)):
                internal_sum += prices_dict[p + i] * consumption_pattern[i]
            sequences[p] = round(internal_sum, 2)    
        except: 
            print("error")
            continue
    return sequences
