from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from custom_components.peaqnext.service.models.next_sensor.next_sensor_data import NextSensorData
from custom_components.peaqnext.service.models.next_sensor.dt_model import DTModel

@dataclass
class NextSensorOverride(NextSensorData):
    _timeout: any = field(init=False, default=None)
    _parsed_timeout: datetime = field(init=False, default=None)
    _override: bool = field(init=False, default=False)
    dt_model: DTModel = field(repr=False, hash=False, compare=False, default_factory=lambda: DTModel)

    @property
    def override(self) -> bool:
        if self.parsed_timeout is None:
            return self._override
        return self.parsed_timeout > self.dt_model.get_dt_now()
    
    @override.setter
    def override(self, override) -> None:
        self._override = override

    @property
    def timeout(self) -> any:
        """timeout as set by the user"""
        return self._timeout

    @timeout.setter
    def timeout(self, timeout) -> None:
        self._timeout = timeout
        self._parsed_timeout = self.parse_timeout(timeout)

    @property
    def parsed_timeout(self) -> datetime|None:
        """parsed timeout used for override-bool"""
        try:
            return self._parsed_timeout
        except:
            return None
    
    @parsed_timeout.setter
    def parsed_timeout(self, timeout) -> None:
        self._parsed_timeout = timeout

    def parse_timeout(self, timeout) -> datetime|None:
        if timeout is None:
            return None
        if isinstance(timeout, int):
            return self.dt_model.get_dt_now()+timedelta(hours=timeout)
        if isinstance(timeout, datetime):
            return timeout
        if isinstance(timeout, date):
            return datetime.combine(timeout, datetime.min.time())
        if isinstance(timeout, str):
            try:
                return datetime.strptime(timeout, "%Y-%m-%dT%H:%M:%S.%f")
            except:
                return None
        return None