from custom_components.peaqnext.service.models.hour_model import HourModel
from datetime import datetime, timedelta, date


async def async_get_hours_sorted(
    prices: list,
    prices_tomorrow: list,
    consumption_pattern: list[float],
    non_hours_start: list[int],
    non_hours_end: list[int],
    duration_in_seconds: int,
    mock_hour: int|None = None,
    mock_date: date|None = None,
    use_cent: bool = False
) -> list[HourModel]:
    _hour = datetime.now().hour if mock_hour is None else mock_hour
    prices_dict = {k: v for k, v in enumerate(prices) if k >= _hour} #todo: this is a problem with late hours.
    prices_dict.update({k + 24: v for k, v in enumerate(prices_tomorrow)})
    sequences = await async_list_all_hours(prices_dict, consumption_pattern)
    _start_date = mock_date if mock_date else datetime.now().date()
    _start = datetime.combine(_start_date, datetime.min.time())
    ret = [] 
    for s in sequences:
        _dt_start = _start +timedelta(hours=s)
        _end = _dt_start + timedelta(seconds=duration_in_seconds)
        if any([
            _end.hour in non_hours_end,
            _end.hour - 24 in non_hours_end,
            s in non_hours_start,
            s - 24 in non_hours_start,
        ]):
            continue
        ret.append(HourModel(
            dt_start=_dt_start,
            dt_end = _end,
            idx=s,
            hour_start=s,
            hour_end=_end.hour,
            price=sequences[s],
            use_cent=use_cent,
            sum_consumption_pattern=sum(consumption_pattern)
        ))
    return list(sorted(ret, key=lambda i: (i.comparer, i.dt_start)))

async def async_cheapest_hour(
    hours_list: list[HourModel], cheapest_cap: int = None, mock_hour: int = None, mock_date: date = None
) -> HourModel:
    _date: date = datetime.now().date() if mock_date is None else mock_date
    _dt = datetime.combine(_date, datetime.min.time())
    _now:datetime = _dt if mock_hour is None else _dt.replace(hour=mock_hour)
    hour_limit = _now + timedelta(hours=cheapest_cap) if cheapest_cap is not None else _now + timedelta(hours=48)
    ret = [v for v in hours_list if v.dt_start < hour_limit]
    try:
        return ret[0]
    except:
        return None


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
