
from enum import Enum
import logging

_LOGGER = logging.getLogger(__name__)


class CalculateBy(Enum):
    STARTTIME = "Start time"
    ENDTIME = "End time"

    def parse_from_config(strtype: str):
        try:
            for f in CalculateBy:
                if strtype == f.value:
                    return f
        except Exception as e:
            _LOGGER.error(f"Unable to parse Calculate-type, invalid value {strtype}: {e}")
            return CalculateBy.STARTTIME