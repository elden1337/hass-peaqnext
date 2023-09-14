from dataclasses import dataclass, field
from custom_components.peaqnext.service.models.next_sensor.enums.calculate_by import CalculateBy
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy

@dataclass
class NextSensorData:
    total_consumption_in_kwh: float|None = None
    total_duration_in_minutes: int|None = None
    custom_consumption_pattern_list: list[int|float] = field(repr=False, hash=False, compare=False, default_factory=lambda: [])
    non_hours_start: list[int] = field(default_factory=lambda: [])
    non_hours_end: list[int] = field(default_factory=lambda: [])
    deduct_price: float = 0
    use_cent: bool = False
    update_by: UpdateBy = UpdateBy.MINUTE
    calculate_by: CalculateBy = CalculateBy.STARTTIME
    show_relative_time: bool = False


    @property
    def total_duration_in_seconds(self) -> int:
        if self.total_duration_in_minutes is None:
            return 0
        return self.total_duration_in_minutes * 60