from dataclasses import dataclass, field
from datetime import datetime, date
from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.segments import (
    async_calculate_consumption_per_hour,
)
from custom_components.peaqnext.service.hours import (
    async_get_hours_sorted,
    cheapest_hour,
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
    default_closest_cheap: int = 12
    use_cent: bool = False
    non_hours_start: list[int] = field(default_factory=lambda: [])
    non_hours_end: list[int] = field(default_factory=lambda: [])
    _all_sequences: list[HourModel] = field(default_factory=lambda: [])
    _mock_hour: int|None = None
    _mock_date: date|None = None
    _mock_minute: int|None = None

    @property
    def best_start(self) -> HourModel:
        return cheapest_hour(
            hours_list=self.all_sequences, 
            cheapest_cap=None,
            mock_dt=self._get_dt_now() 
            )

    @property
    def best_close_start(self) -> HourModel:
        return cheapest_hour(
            hours_list=self.all_sequences, 
            cheapest_cap=self.default_closest_cheap, 
            mock_dt=self._get_dt_now() 
            )

    @property
    def all_sequences(self) -> list[HourModel]:
        return [h for h in self._all_sequences if h.dt_start >= self._get_dt_now()]

    def _get_dt_now(self) -> datetime:
        """returns start of current hour, mockhour and date if applicable."""
        _hour = self._mock_hour if self._mock_hour is not None else datetime.now().hour
        _minute = self._mock_minute if self._mock_minute is not None else datetime.now().minute
        _date = self._mock_date if self._mock_date is not None else datetime.now().date()
        return datetime.combine(_date, datetime.min.time()).replace(hour=_hour, minute=_minute)
        
    def set_hour(self, hour) -> None:
        self._mock_hour = hour

    def set_date(self, date) -> None:
        self._mock_date = date

    def set_minute(self, minute) -> None:
        self._mock_minute = minute

    async def async_update_sensor(self, prices: tuple[list,list], use_cent:bool = False) -> None:
        self.use_cent = use_cent
        segments: list = await async_calculate_consumption_per_hour(
            self.total_consumption_in_kwh,
            self.total_duration_in_seconds,
            self.consumption_type,
        )
        try:            
            self._all_sequences = await async_get_hours_sorted(
                prices=prices,
                consumption_pattern=segments,
                non_hours_start=self.non_hours_start,
                non_hours_end=self.non_hours_end,
                duration_in_seconds=self.total_duration_in_seconds,
                mock_dt =self._get_dt_now(),
                use_cent=self.use_cent
            )
        except Exception as e:
            _LOGGER.error(
                f"Unable to calculate best hours for sensor: {self.hass_entity_id}. Exception: {e}"
            )
