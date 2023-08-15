from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from custom_components.peaqnext.service.models.next_sensor.next_sensor_data import NextSensorData

@dataclass
class NextSensorOverride(NextSensorData):
    #timeout: any = None
    _timeout: datetime = field(init=False, default=None)
    _parsed_timeout: datetime = field(init=False, default=None)
    override: bool = field(default=False)

    @property
    def timeout(self) -> datetime|None:
        return self._timeout

    @timeout.setter
    def timeout(self, timeout) -> None:
        self._timeout = timeout
        self._parsed_timeout = self.parse_timeout(timeout)

    @property
    def parsed_timeout(self) -> datetime|None:
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
            return datetime.now()+timedelta(hours=timeout)
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