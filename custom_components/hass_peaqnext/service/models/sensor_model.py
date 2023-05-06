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


@dataclass
class NextSensor:
    consumption_type: ConsumptionType
    name: str
    hass_entity_id: str
    total_duration_in_seconds: int
    total_consumption_in_kwh: float
    _best_start: HourModel = field(init=False)
    _best_close_start: HourModel = field(init=False)
    _all_sequences: list[HourModel] = field(default_factory=lambda: [])

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
        all_hours_model = await async_get_hours_sorted(prices[0], prices[1], segments)
        self._best_start = all_hours_model[0]
        self._best_close_start = await async_cheapest_close_hour(all_hours_model)
        self._all_sequences = all_hours_model
