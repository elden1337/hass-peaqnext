from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
import logging

CONSUMPTIONCONVERSION = {
    ConsumptionType.Flat: [1],
    ConsumptionType.PeakIn: [2, 1, 1, 1],
    ConsumptionType.PeakOut: [1, 1, 1, 2],
    ConsumptionType.MidPeak: [1, 1, 2, 1, 1],
    ConsumptionType.PeakInOut: [2, 1, 1, 2],
    ConsumptionType.Custom: []
}

_LOGGER = logging.getLogger(__name__)


def calculate_consumption_per_hour(
    consumption: float, duration_in_seconds: int, consumption_type: ConsumptionType, custom_consumption_pattern: list, start_minute: int
) -> list[float]:
    # if 4 < duration_in_seconds <= 3600:
    #     return [consumption]
    try:
        segments = _get_segments(consumption_type, duration_in_seconds, custom_consumption_pattern)
    except Exception as e:
        _LOGGER.error(f"Unable to get segments for sensor. Exception: {e}")
        return [consumption]
    try:
        minute_consumption = _get_minute_consumption(segments, consumption)
        duration_in_minutes = int(duration_in_seconds / 60)
    except Exception as e:
        _LOGGER.error(f"Unable to get minute consumption for sensor. Exception: {e}")
        return [consumption]
    ret = []
    try:
        intret = 0
        j = 0
        for t in range(start_minute, duration_in_minutes+start_minute):
            intret += minute_consumption[j]
            if (t % 60 == 0 and t > 0) or t == duration_in_minutes+start_minute - 1:
                ret.append(round(intret, 1))
                intret = 0
            j += 1
    except Exception as e:
        print(e)
    print(f"ret: {ret}")
    return ret


def _get_minute_consumption(
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


def _get_segments(
    consumption_type: ConsumptionType, duration_in_seconds: int, custom_consumption_pattern: list
) -> dict:
    if consumption_type == ConsumptionType.Custom:
        segments = custom_consumption_pattern
    else:
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


