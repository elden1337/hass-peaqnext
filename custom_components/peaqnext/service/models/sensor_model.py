from dataclasses import dataclass, field
from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.segments import (
    async_calculate_consumption_per_hour,
)
from custom_components.peaqnext.service.hours import (
    async_get_hours_sorted,
    async_cheapest_close_hour,
)
from custom_components.peaqnext.service.models.hour_model import HourModel
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class NextSensor:
    consumption_type: ConsumptionType
    name: str
    hass_entity_id: str
    total_duration_in_seconds: int
    total_consumption_in_kwh: float
    non_hours_start: list[int] = field(default_factory=lambda: [])
    non_hours_end: list[int] = field(default_factory=lambda: [])
    _best_start: HourModel = field(init=False)
    _best_close_start: HourModel = field(init=False)
    _all_sequences: list[HourModel] = field(default_factory=lambda: [])
    _end_minute: int = field(init=False)

    def __post_init__(self) -> None:
        self._best_start = HourModel(0, 0, 0, 0, 0, 0)
        self._best_close_start = HourModel(0, 0, 0, 0, 0, 0)
        self._all_sequences = []
        self._end_minute = 0

    @property
    def end_minute(self) -> int:
        return self._end_minute

    @property
    def best_start(self) -> HourModel:
        return self._best_start

    @property
    def best_close_start(self) -> HourModel:
        return self._best_close_start

    @property
    def all_sequences(self) -> list[HourModel]:
        return self._all_sequences

    async def async_update_sensor(self, prices: list) -> None:
        segments: list = await async_calculate_consumption_per_hour(
            self.total_consumption_in_kwh,
            self.total_duration_in_seconds,
            self.consumption_type,
        )
        try:
            all_hours_model = await async_get_hours_sorted(
                prices[0], prices[1], segments, self.non_hours_start, self.non_hours_end
            )
            self._best_start = all_hours_model[list(all_hours_model.keys())[0]]
            self._end_minute = await self.async_get_end_minute()
            self._best_close_start = await async_cheapest_close_hour(all_hours_model)
            self._all_sequences = list(all_hours_model.values())
        except Exception as e:
            _LOGGER.error(
                f"Unable to calculate best hours for sensor: {self.hass_entity_id}. Exception: {e}"
            )
            return

    async def async_get_end_minute(self) -> int:
        full_hours = (self.total_duration_in_seconds / 60) % 60
        return self.total_duration_in_seconds - 60 * full_hours
