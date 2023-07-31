from custom_components.peaqnext.service.models.hour_model import HourModel
from datetime import datetime, timedelta


async def async_get_hours_sorted(
    prices: list,
    prices_tomorrow: list,
    consumption_pattern: list[float],
    non_hours_start: list[int],
    non_hours_end: list[int],
    duration_in_seconds: int,
    mock_hour: int = None,
    use_cent: bool = False
) -> dict[int, HourModel]: #todo: rewrite to a list instead. dict not needed and is just complicating things. Also, sort after comparer-total (create that) and thenby datetime
    _hour = mock_hour or datetime.now().hour    
    prices_dict = {k: v for k, v in enumerate(prices) if k >= _hour}
    prices_dict.update({k + 24: v for k, v in enumerate(prices_tomorrow)})
    sequences = await async_list_all_hours(
        prices_dict, consumption_pattern#, non_hours_start, non_hours_end
    )
    
    ret = {} 
    for s in sequences:
        _end = get_end(s, duration_in_seconds)
        if (s or s-24) not in non_hours_start and (_end.hour or _end.hour - 24) not in non_hours_end:
            ret[s] = HourModel(
                sum_consumption_pattern=sum(consumption_pattern),
                idx=s,
                hour_start=s,
                hour_end=_end.hour,
                price=sequences[s],
                use_cent=use_cent
            )
    return dict(sorted(ret.items(), key=lambda i: i[1].price))

def get_end(loop_index: int, duration_in_seconds:int) -> datetime:
    _start = datetime.now()
    #_start = _start + timedelta(days=1)
    _start = (
        _start.replace(hour=loop_index - (24*(loop_index > 23)))
        .replace(minute=0)
        .replace(second=0)
        .replace(microsecond=0)
    )
    return _start + timedelta(seconds=duration_in_seconds)

async def async_cheapest_close_hour(
    hours_dict: dict[int, HourModel], mock_hour: int = None
) -> HourModel:
    """returns the cheapeast hour that is less than 12hrs from now."""
    _hour = mock_hour or datetime.now().hour
    hour_limit = _hour + 12
    ret = [v for k, v in hours_dict.items() if k < hour_limit]
    return ret[0]


async def async_list_all_hours(
    prices_dict: dict,
    consumption_pattern: list,
    # non_hours_start: list,
    # non_hours_end: list,
) -> dict:
    sequences = {}
    for p in prices_dict:
        if p + len(consumption_pattern) - 1 > max([h for h in prices_dict.keys()]):
            break
        # if p in non_hours_start or p - 24 in non_hours_start:
        #     continue
        # if (
        #     p + len(consumption_pattern) - 1 in non_hours_end
        #     or p - 24 + len(consumption_pattern) - 1 in non_hours_end
        # ):
        #     print(f"endhour detected: {p + len(consumption_pattern) - 1} {non_hours_end}")
        #     continue
        internal_sum = 0
        for i in range(0, len(consumption_pattern)):
            internal_sum += prices_dict[p + i] * consumption_pattern[i]
        sequences[p] = round(internal_sum, 2)    
    return sequences
