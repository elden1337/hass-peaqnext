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
) -> dict[int, HourModel]: #todo: rewrite to a list instead. dict not needed and is just complicating things. Also, sort after comparer-total (create that) and thenby datetime
    _hour = datetime.now().hour if mock_hour is None else mock_hour
    prices_dict = {k: v for k, v in enumerate(prices) if k >= _hour} #todo: this is a problem with late hours.
    prices_dict.update({k + 24: v for k, v in enumerate(prices_tomorrow)})
    sequences = await async_list_all_hours(prices_dict, consumption_pattern)
    _start_date = mock_date if mock_date else datetime.now().date()
    _start = datetime(_start_date.year, _start_date.month, _start_date.day, _hour, 0, 0, 0)
    ret = {} 
    hour_cycle = 0
    for s in sequences:
        _dt_start = _start +timedelta(hours=hour_cycle)
        _end = _dt_start + timedelta(seconds=duration_in_seconds)
        hour_cycle += 1
        if _end.hour in non_hours_end:
            continue
        if _end.hour - 24 in non_hours_end:
            continue
        if s in non_hours_start:
            continue
        if s - 24 in non_hours_start:
            continue
        ret[s] = HourModel(
            dt_start=_dt_start,
            dt_end = _end,
            idx=s,
            hour_start=s,
            hour_end=_end.hour,
            price=sequences[s],
            use_cent=use_cent,
            sum_consumption_pattern=sum(consumption_pattern)
        )
        
    return dict(sorted(ret.items(), key=lambda i: i[1].price))

async def async_cheapest_close_hour(
    hours_dict: dict[int, HourModel], cheapest_cap: int, mock_hour: int = None
) -> HourModel:
    """returns the cheapeast hour that is less than 12hrs from now."""
    _hour = mock_hour or datetime.now().hour
    hour_limit = _hour + cheapest_cap
    ret = [v for k, v in hours_dict.items() if k < hour_limit]
    return ret[0]


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
