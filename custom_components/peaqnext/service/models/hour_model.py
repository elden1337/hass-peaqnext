from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class HourModel:
    idx: int
    price: float    
    dt_start: datetime = field(default_factory=lambda: datetime.now().replace(second=0).replace(microsecond=0))
    dt_end: datetime = field(default_factory=lambda: datetime.now().replace(second=0).replace(microsecond=0))
    use_cent: bool = False
    sum_consumption_pattern: int = -1
    comparer_addition: bool = False
    is_valid: bool = True
    perkwh: float = field(init=False)
    comparer: float = field(init=False) 

    def __post_init__(self):
        if self.use_cent:            
            self.price = round(self.price/100,2)        
        self.perkwh=round(self.price / self.sum_consumption_pattern, (2+int(self.comparer_addition)))
        self.comparer=round(self.price,(1+int(self.comparer_addition)))
