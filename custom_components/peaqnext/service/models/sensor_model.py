from dataclasses import dataclass, field
from datetime import datetime
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
    use_cent: bool = False
    non_hours_start: list[int] = field(default_factory=lambda: [])
    non_hours_end: list[int] = field(default_factory=lambda: [])
    _best_start: HourModel = field(init=False)
    _best_close_start: HourModel = field(init=False)
    _all_sequences: list[HourModel] = field(default_factory=lambda: [])
    _mock_hour: int = datetime.now().hour

    def __post_init__(self) -> None:
        self._best_start = HourModel(0, 0, 0, 0)
        self._best_close_start = HourModel(0, 0, 0, 0)
        self._all_sequences = []

    @property
    def best_start(self) -> HourModel:
        return self._best_start

    @property
    def best_close_start(self) -> HourModel:
        return self._best_close_start

    @property
    def all_sequences(self) -> list[HourModel]:
        return self._all_sequences

    def set_hour(self, hour) -> None:
        self._mock_hour = hour

    async def async_update_sensor(self, prices: list, use_cent:bool = False) -> None:
        self.use_cent = use_cent
        segments: list = await async_calculate_consumption_per_hour(
            self.total_consumption_in_kwh,
            self.total_duration_in_seconds,
            self.consumption_type,
        )
        try:            
            all_hours_model = await async_get_hours_sorted(
                prices=prices[0],
                prices_tomorrow=prices[1],
                consumption_pattern=segments,
                non_hours_start=self.non_hours_start,
                non_hours_end=self.non_hours_end,
                duration_in_seconds=self.total_duration_in_seconds,
                mock_hour=self._mock_hour,
                use_cent=self.use_cent
            ) 
            for i in all_hours_model.items():
                print(i)
            self._best_start = all_hours_model[list(all_hours_model.keys())[0]]
            self._best_close_start = await async_cheapest_close_hour(all_hours_model)
            self._all_sequences = list(all_hours_model.values())
        except Exception as e:
            _LOGGER.error(
                f"Unable to calculate best hours for sensor: {self.hass_entity_id}. Exception: {e}"
            )
            return
