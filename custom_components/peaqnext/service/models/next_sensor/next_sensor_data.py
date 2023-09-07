from dataclasses import dataclass, field

@dataclass
class NextSensorData:
    total_consumption_in_kwh: float|None = None
    total_duration_in_minutes: int|None = None
    custom_consumption_pattern_list: list[int|float] = field(repr=False, hash=False, compare=False, default_factory=lambda: [])
    non_hours_start: list[int] = field(default_factory=lambda: [])
    non_hours_end: list[int] = field(default_factory=lambda: [])
    deduct_price: float = 0
    use_cent: bool = False
    update_minute: bool = True

    @property
    def total_duration_in_seconds(self) -> int:
        if self.total_duration_in_minutes is None:
            return 0
        return self.total_duration_in_minutes * 60