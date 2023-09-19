from dataclasses import dataclass, field
from datetime import datetime, timedelta
from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.models.next_sensor.dt_model import DTModel
from custom_components.peaqnext.service.models.next_sensor.enums.calculate_by import CalculateBy
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy
from custom_components.peaqnext.service.models.next_sensor.next_sensor_data import NextSensorData
from custom_components.peaqnext.service.models.next_sensor.next_sensor_override import NextSensorOverride
from custom_components.peaqnext.service.models.sensor_prices import SensorPrices
from custom_components.peaqnext.service.segments import (
    calculate_consumption_per_hour,
)
from custom_components.peaqnext.service.hours import (
    get_hours_sorted,
    cheapest_hour,
)
from custom_components.peaqnext.service.models.hour_model import HourModel
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class NextSensor(NextSensorData):
    consumption_type: ConsumptionType = ConsumptionType.Flat  
    name: str = "Next Sensor"
    hass_entity_id: str = "sensor.next_sensor"
    custom_consumption_pattern: str|None = field(repr=False, hash=False, compare=False, default=None)
    default_closest_cheap: int = 12
    _all_sequences: list[HourModel] = field(default_factory=lambda: [])
    dt_model: DTModel = field(default_factory=lambda: DTModel())
    price_model: SensorPrices = field(default_factory=lambda: SensorPrices())
    override_model: NextSensorOverride = field(default_factory=lambda: NextSensorOverride())
    override: bool = field(default=False)
    _latest_update: int = field(default=None, init=True, repr=False, hash=False, compare=False)

    def __post_init__(self):
        self.custom_consumption_pattern_list = self._validate_custom_pattern(self.custom_consumption_pattern)
        self.override_model = NextSensorOverride(
            total_consumption_in_kwh=self.total_consumption_in_kwh, 
            total_duration_in_minutes=self.total_duration_in_minutes, 
            custom_consumption_pattern_list=self.custom_consumption_pattern_list, 
            non_hours_start=self.non_hours_start, 
            non_hours_end=self.non_hours_end,
            dt_model=self.dt_model,
            deduct_price=self.deduct_price,
            use_cent=self.use_cent, 
            update_by=self.update_by,
            calculate_by=self.calculate_by
            )

    def __getattribute__(self, attr):
        """Custom override for getattr that resolves either the overriden data or the regular."""
        self_override = object.__getattribute__(self, 'override')
        override_model = super().__getattribute__('override_model')
        if self_override != getattr(override_model, 'override'):
            self.override = getattr(override_model, 'override')
            return self.__getattribute__(attr)
        if self_override and hasattr(override_model, attr) and attr in NextSensorData.__dict__:
            return getattr(override_model, attr)
        return super().__getattribute__(attr)
  
    def _validate_custom_pattern(self, custom_consumption_pattern: str|None) -> list[int|float]:
        if not custom_consumption_pattern:
            return []
        pattern = custom_consumption_pattern.split(",")
        try:
            pattern = [float(x) for x in pattern]
        except Exception as e:
            raise Exception(f"Invalid custom consumption pattern provided: {e}")
        return pattern  

    @property
    def best_start(self) -> HourModel:
        return cheapest_hour(
            hours_list=self.all_sequences, 
            cheapest_cap=None,
            override_end=self._get_end_cap(),
            mock_dt=self.dt_model.get_dt_now()
            )

    @property
    def best_close_start(self) -> HourModel:
        return cheapest_hour(
            hours_list=self.all_sequences, 
            cheapest_cap=self.default_closest_cheap, 
            override_end=self._get_end_cap(),
            mock_dt=self.dt_model.get_dt_now()
            )

    @property
    def all_sequences(self) -> list[HourModel]:
        _now = self.dt_model.get_dt_now()
        if self.update_by == UpdateBy.HOUR:
            _now = _now.replace(minute=0, second=0, microsecond=0)
        return [h for h in self._all_sequences if h.dt_start >= _now and h.is_valid and (self._get_end_cap() is None or h.dt_end < self._get_end_cap())]

    async def async_update_sensor(self, prices: tuple[list,list], use_cent:bool = False, currency:str = "sek") -> None:
        if self._should_update():
            self._update_sensor(prices, use_cent, currency)

    def _should_update(self) -> bool:
        deltadiff = {
            1: timedelta(minutes=1),
            0: timedelta(hours=1),
        }
        new = self.dt_model.get_dt_now()
        if self._latest_update is None:
            self._latest_update = new
            return True
        if self._latest_update != new:
            if new >= self._latest_update + deltadiff[int(self.update_by == UpdateBy.MINUTE)]:
                self._latest_update = new
                return True
        return False

    def _update_sensor(self, prices: tuple[list,list], use_cent:bool = False, currency:str = "sek") -> None:
        self.price_model.use_cent = use_cent
        self.price_model.prices = prices
        self.price_model.currency = currency
        self._update_sensor_internal()        

    def _update_sensor_internal(self) -> None:
        segments: list = calculate_consumption_per_hour(
            self.total_consumption_in_kwh,
            self.total_duration_in_seconds,
            self.consumption_type,
            self.custom_consumption_pattern_list,
            self.dt_model.get_dt_now().minute if self.update_by == UpdateBy.MINUTE else 0
        )
        try:            
            self._all_sequences = get_hours_sorted(
                prices=tuple([p - self.deduct_price for p in price_list] for price_list in self.price_model.prices),
                consumption_pattern=segments,
                non_hours_start=self.non_hours_start,
                non_hours_end=self.non_hours_end,
                duration_in_seconds=self.total_duration_in_seconds,
                mock_dt =self.dt_model.get_dt_now(),
                use_cent=self.price_model.use_cent,
                currency=self.price_model.currency,
                update_per_minute=(self.update_by == UpdateBy.MINUTE),
                calculate_end = (self.calculate_by == CalculateBy.ENDTIME)
            )
        except Exception as e:
            _LOGGER.error(
                f"Unable to calculate best hours for sensor: {self.hass_entity_id}. Exception: {e}"
            )

    def _get_end_cap(self) -> datetime|None: 
        if self.override and self.override_model.parsed_timeout is not None:
            _LOGGER.debug(f"Using override timeout which is: {self.override_model.parsed_timeout}")
            return self.override_model.parsed_timeout
        return None

    async def async_override_sensor_data(
            self,
            total_consumption_in_kwh: float|None = None, 
            total_duration_in_minutes: int|None = None,
            custom_consumption_pattern: str|None = None,
            non_hours_start: list[int]|None = None,
            non_hours_end: list[int]|None = None,
            timeout: any = None
            ) -> None:
            do_override: bool = False
            self.override_model.timeout = timeout
            pattern = self._validate_custom_pattern(custom_consumption_pattern)
            if len(pattern) > 0:
                do_override = True
                self.override_model.custom_consumption_pattern_list = pattern
            if total_consumption_in_kwh is not None:
                do_override = True
                self.override_model.total_consumption_in_kwh = total_consumption_in_kwh
            if total_duration_in_minutes is not None:
                do_override = True
                self.override_model.total_duration_in_minutes = total_duration_in_minutes
            if non_hours_start is not None:
                do_override = True
                self.override_model.non_hours_start = non_hours_start
            if non_hours_end is not None:
                do_override = True
                self.override_model.non_hours_end = non_hours_end
            self.override_model.override = do_override
            self.override = do_override
            self._update_sensor_internal()

    async def async_cancel_override(self) -> None:
        self.override_model = NextSensorOverride(
            total_consumption_in_kwh=self.total_consumption_in_kwh, 
            total_duration_in_minutes=self.total_duration_in_minutes, 
            custom_consumption_pattern_list=self.custom_consumption_pattern_list, 
            non_hours_start=self.non_hours_start, 
            non_hours_end=self.non_hours_end,
            dt_model=self.dt_model
            )
        self._update_sensor_internal()



    
    