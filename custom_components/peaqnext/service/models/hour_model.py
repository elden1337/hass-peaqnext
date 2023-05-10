from dataclasses import dataclass, field


@dataclass
class HourModel:
    idx: int
    price: float
    perkwh: float
    comparer: float
    hour_start: int
    hour_end: int
    minute_end: int = 0

    def __post_init__(self):
        self._hour_start = self.hour_start
        self._hour_end = self.hour_end

    @property
    def hour_start(self):
        return self._hour_start

    @hour_start.setter
    def hour_start(self, value):
        self._hour_start = value if value < 24 else value - 24

    @property
    def hour_end(self):
        return self._hour_end

    @hour_end.setter
    def hour_end(self, value):
        self._hour_end = value if value < 24 else value - 24
