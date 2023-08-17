from enum import Enum


class ConsumptionType(Enum):
    Flat = "Flat consumption"
    PeakIn = "Peak in beginning"
    PeakOut = "Peak in end"
    MidPeak = "Peak in middle"
    PeakInOut = "Peak in beginning and end"
    Custom = "Custom consumption"


CONSUMPTIONTYPE_NAMES = [e.value for e in ConsumptionType]
