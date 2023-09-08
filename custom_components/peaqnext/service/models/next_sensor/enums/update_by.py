
from enum import Enum
import logging

_LOGGER = logging.getLogger(__name__)


class UpdateBy(Enum):
    MINUTE = "Every minute"
    HOUR = "Every hour"

    def parse_from_config(strtype: str):
        try:
            for f in UpdateBy:
                if strtype == f.value:
                    return f
        except Exception as e:
            _LOGGER.error(f"Unable to parse UpdateBy-type, invalid value {strtype}: {e}")
            return UpdateBy.MINUTE