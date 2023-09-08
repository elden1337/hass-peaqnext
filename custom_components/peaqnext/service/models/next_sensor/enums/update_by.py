
from enum import Enum
import logging

_LOGGER = logging.getLogger(__name__)


class UpdateBy(Enum):
    MINUTE = "Every minute"
    HOUR = "Every hour"
