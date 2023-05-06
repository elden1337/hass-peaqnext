from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)

CONSUMPTIONCONVERSION = {
    ConsumptionType.Flat: [1],
    ConsumptionType.PeakIn: [2, 1, 1, 1],
    ConsumptionType.PeakOut: [1, 1, 1, 2],
    ConsumptionType.MidPeak: [1, 1, 2, 1, 1],
    ConsumptionType.PeakInOut: [2, 1, 1, 2],
}


async def async_calculate_consumption_per_hour(
    consumption: float, duration_in_seconds: int, consumption_type: ConsumptionType
) -> list[float]:
    if 4 < duration_in_seconds <= 3600:
        return [consumption]
    segments = await async_get_segments(consumption_type, duration_in_seconds)
    minute_consumption = await async_get_minute_consumption(segments, consumption)
    duration_in_minutes = int(duration_in_seconds / 60)
    ret = []
    try:
        intret = 0
        for t in range(0, duration_in_minutes):
            intret += minute_consumption[t]
            if (t % 60 == 0 and t > 0) or t == duration_in_minutes - 1:
                ret.append(round(intret, 1))
                intret = 0
    except Exception as e:
        print(e)
    return ret


async def async_get_minute_consumption(
    segments: dict, total_consumption: float
) -> list[float]:
    consumption_pattern = {
        k: (round(v[0] * total_consumption, 1), v[1]) for k, v in segments.items()
    }
    ret = []
    for k, v in consumption_pattern.items():
        for i in range(int(v[1] / 60)):
            ret.append(v[0] / (v[1] / 60))
    return ret


async def async_get_segments(
    consumption_type: ConsumptionType, duration_in_seconds: int
) -> dict:
    segments = CONSUMPTIONCONVERSION.get(consumption_type)
    segment = 1
    ret = {}
    segment_duration = int(duration_in_seconds / len(segments) / 60) * 60
    total_draw = sum(segments)
    for s in segments:
        ret[segment] = (s / total_draw, segment_duration)
        segment += 1
    if sum([x[1] for x in ret.values()]) < duration_in_seconds:
        missing = duration_in_seconds - sum([x[1] for x in ret.values()])
        r0 = ret[1][0]
        r1 = ret[1][1] + missing
        ret[1] = (r0, r1)
    return ret
