from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class HourModel:
    idx: int
    price: float    
    hour_start: int
    hour_end: int
    dt_start: datetime = field(default_factory=lambda: datetime.now().replace(second=0).replace(microsecond=0))
    dt_end: datetime = field(default_factory=lambda: datetime.now().replace(second=0).replace(microsecond=0))
    use_cent: bool = False
    sum_consumption_pattern: int = 1
    perkwh: float = field(init=False)
    comparer: float = field(init=False) 

    def __post_init__(self):        
        self._hour_start = self.hour_start
        self._hour_end = self.hour_end
        if self.use_cent:            
            self.price = round(self.price/100,2)        
        self.perkwh=round(self.price / self.sum_consumption_pattern, 2)
        self.comparer=round(self.price,1)

    @property
    def hour_start(self):
        return self._hour_start

    @hour_start.setter
    def hour_start(self, value):
        self._hour_start = value if value < 24 else value - 24

    @property
    def hour_end(self):
        return self._hour_end

    @hour_end.setter
    def hour_end(self, value):
        self._hour_end = value if value < 24 else value - 24
