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
) -> dict[int, HourModel]:
    _hour = mock_hour if mock_hour else datetime.now().hour
    prices_dict = {k: v for k, v in enumerate(prices) if k >= _hour}
    prices_dict.update({k + 24: v for k, v in enumerate(prices_tomorrow)})
    sequences = await async_list_all_hours(
        prices_dict, consumption_pattern, non_hours_start, non_hours_end
    )

    ret = {}
    for s in sequences:
        # new func
        if s <= 23:
            _start = datetime.now()
            _start = (
                _start.replace(hour=s)
                .replace(minute=0)
                .replace(second=0)
                .replace(microsecond=0)
            )
            _end = _start + timedelta(seconds=duration_in_seconds)
        else:
            _start = datetime.now()
            _start = _start + timedelta(days=1)
            _start = (
                _start.replace(hour=s - 24)
                .replace(minute=0)
                .replace(second=0)
                .replace(microsecond=0)
            )
            _end = _start + timedelta(seconds=duration_in_seconds)
        # new func
        ret[s] = HourModel(
            idx=s,
            hour_start=s,
            hour_end=_end.hour,
            price=sequences[s],
            perkwh=round(sequences[s] / sum(consumption_pattern), 2),
            comparer=round(sequences[s] / sum(consumption_pattern), 1),
        )
    return dict(sorted(ret.items(), key=lambda i: i[1].comparer))


async def async_cheapest_close_hour(
    hours_dict: dict[int, HourModel], mock_hour: int = None
) -> HourModel:
    """returns the cheapeast hour that is less than 12hrs from now."""
    _hour = mock_hour if mock_hour else datetime.now().hour
    hour_limit = _hour + 12
    ret = [v for k, v in hours_dict.items() if k < hour_limit]
    return ret[0]


async def async_list_all_hours(
    prices_dict: dict,
    consumption_pattern: list,
    non_hours_start: list,
    non_hours_end: list,
) -> dict:
    sequences = {}
    for p in prices_dict:
        if p + len(consumption_pattern) - 1 > max([h for h in prices_dict.keys()]):
            break
        if p in non_hours_start or p - 24 in non_hours_start:
            continue
        if (
            p + len(consumption_pattern) - 1 in non_hours_end
            or p - 24 + len(consumption_pattern) - 1 in non_hours_end
        ):
            continue
        internal_sum = 0
        for i in range(0, len(consumption_pattern)):
            internal_sum += prices_dict[p + i] * consumption_pattern[i]
        sequences[p] = round(internal_sum, 2)
    return sequences
