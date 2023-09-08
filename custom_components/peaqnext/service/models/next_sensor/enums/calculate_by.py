
from enum import Enum
import logging

_LOGGER = logging.getLogger(__name__)


class CalculateBy(Enum):
    STARTTIME = "Start time"
    ENDTIME = "End time"
