from dataclasses import dataclass, field
from datetime import datetime, date
from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.models.dt_model import DTModel
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
class NextSensorData:
    total_consumption_in_kwh: float|None = None
    total_duration_in_minutes: int|None = None
    custom_consumption_pattern_list: list[int|float] = field(repr=False, hash=False, compare=False, default_factory=lambda: [])
    non_hours_start: list[int] = field(default_factory=lambda: [])
    non_hours_end: list[int] = field(default_factory=lambda: [])

    @property
    def total_duration_in_seconds(self) -> int:
        if self.total_duration_in_minutes is None:
            return 0
        return self.total_duration_in_minutes * 60
    
@dataclass
class NextSensorOverride(NextSensorData):
    timeout: any = None
    _timeout: any = field(init=False, default=None)
    override: bool = field(default=False)

    def __post_init__(self):
        # if self.timeout is None:
        #     self._override = True
        pass

    def set_timeout(self, timeout) -> None:
        pass

@dataclass
class NextSensor(NextSensorData, object):
    consumption_type: ConsumptionType = ConsumptionType.Flat  
    name: str = "Next Sensor"
    hass_entity_id: str = "sensor.next_sensor"
    custom_consumption_pattern: str|None = field(repr=False, hash=False, compare=False, default=None)
    default_closest_cheap: int = 12
    _all_sequences: list[HourModel] = field(default_factory=lambda: [])
    dt_model: DTModel = field(default_factory=lambda: DTModel())
    price_model: SensorPrices = field(default_factory=lambda: SensorPrices())
    override: NextSensorOverride = field(default_factory=lambda: NextSensorOverride())

    def __getattribute__(self, attr):
        print(object.__getattribute__(self.override, 'override'))
        # if bool(object.__getattribute__('override').__getattribute__('override')) == True:
        #     #if attr == 'total_consumption_in_kwh':
        #         #print(f"getting from override: {self.override.__getattribute__(attr)}. raw is: {self.override.total_consumption_in_kwh}")
        #     print(f"returning: {object.__getattribute__('override').__getattribute__(attr)}")
        #     return object.__getattribute__('override').__getattribute__(attr)
        # else:
        return object.__getattribute__(self, attr)

    def __post_init__(self):
        self.custom_consumption_pattern_list = self._validate_custom_pattern(self.custom_consumption_pattern)

    def _validate_custom_pattern(self, custom_consumption_pattern: str) -> list[int|float]:
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
            mock_dt=self.dt_model.get_dt_now() 
            )

    @property
    def best_close_start(self) -> HourModel:
        return cheapest_hour(
            hours_list=self.all_sequences, 
            cheapest_cap=self.default_closest_cheap, 
            mock_dt=self.dt_model.get_dt_now()
            )

    @property
    def all_sequences(self) -> list[HourModel]:
        return [h for h in self._all_sequences if h.dt_start >= self.dt_model.get_dt_now()]

    def set_hour(self, hour) -> None:
        self.dt_model.mock_hour = hour

    def set_date(self, date) -> None:
        self.dt_model.mock_date = date

    def set_minute(self, minute) -> None:
        self.dt_model.mock_minute = minute

    async def async_update_sensor(self, prices: tuple[list,list], use_cent:bool = False, currency:str = "sek") -> None:
        self._update_sensor(prices, use_cent, currency)

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
            self.custom_consumption_pattern_list
        )
        try:            
            self._all_sequences = get_hours_sorted(
                prices=self.price_model.prices,
                consumption_pattern=segments,
                non_hours_start=self.non_hours_start,
                non_hours_end=self.non_hours_end,
                duration_in_seconds=self.total_duration_in_seconds,
                mock_dt =self.dt_model.get_dt_now(),
                use_cent=self.price_model.use_cent,
                currency=self.price_model.currency,
            )
        except Exception as e:
            _LOGGER.error(
                f"Unable to calculate best hours for sensor: {self.hass_entity_id}. Exception: {e}"
            )

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
            override_model = NextSensorOverride(custom_consumption_pattern_list=self.custom_consumption_pattern_list, 
                                                total_consumption_in_kwh=self.total_consumption_in_kwh, 
                                                total_duration_in_minutes=self.total_duration_in_minutes, 
                                                non_hours_start=self.non_hours_start, 
                                                non_hours_end=self.non_hours_end, 
                                                timeout=timeout)
            pattern = self._validate_custom_pattern(custom_consumption_pattern)
            if len(pattern) > 0:
                do_override = True
                override_model.custom_consumption_pattern_list = pattern
            if total_consumption_in_kwh is not None:
                do_override = True
                override_model.total_consumption_in_kwh = total_consumption_in_kwh
            if total_duration_in_minutes is not None:
                do_override = True
                override_model.total_duration_in_minutes = total_duration_in_minutes
            if non_hours_start is not None:
                do_override = True
                override_model.non_hours_start = non_hours_start
            if non_hours_end is not None:
                do_override = True
                override_model.non_hours_end = non_hours_end
            override_model.override = do_override
            self.override = override_model
            print(f"override: {self.override.override}. {do_override}. {self.override.total_consumption_in_kwh}")
            self._update_sensor_internal()

    async def async_cancel_override(self) -> None:
        self.override = NextSensorOverride()
        self._update_sensor_internal()



    
    