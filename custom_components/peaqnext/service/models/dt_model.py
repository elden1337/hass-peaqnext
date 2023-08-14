from dataclasses import dataclass
from datetime import datetime, date

@dataclass
class DTModel:
    mock_hour: int|None = None
    mock_date: date|None = None
    mock_minute: int|None = None

    def get_dt_now(self) -> datetime:
        """returns start of current hour, mockhour and date if applicable."""
        _hour = self.mock_hour if self.mock_hour is not None else datetime.now().hour
        _minute = self.mock_minute if self.mock_minute is not None else datetime.now().minute
        _date = self.mock_date if self.mock_date is not None else datetime.now().date()
        return datetime.combine(_date, datetime.min.time()).replace(hour=_hour, minute=_minute, second=0)
