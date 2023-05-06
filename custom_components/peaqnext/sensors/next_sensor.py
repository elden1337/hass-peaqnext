"""sensor implementation goes here"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..const import DOMAIN, HUB

if TYPE_CHECKING:
    from custom_components.peaqnext.service.hub import Hub
from homeassistant.components.sensor import SensorEntity
import logging
from custom_components.peaqnext.service.models.hour_model import HourModel
from custom_components.peaqnext.util import nametoid

_LOGGER = logging.getLogger(__name__)


class PeaqNextSensor(SensorEntity):
    should_poll = True

    def __init__(self, hub: Hub, entry_id, given_name):
        self.given_name = given_name
        name = f"{hub.hubname} {given_name}"
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True
        self._state: str = None
        self._all_seqeuences = None
        self._next_close = None

    @property
    def state(self) -> float:
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:cash-refund"

    async def async_update(self) -> None:
        status = await self.hub.async_get_updates(nametoid(self.given_name))
        self._state = status["state"]
        self._all_seqeuences = status["all_sequences"]
        self._next_close = status["next_close"]

    @property
    def extra_state_attributes(self) -> dict:
        # todo: fix attr for persisting the consumption-dict and connected-at
        attr_dict = {
            "Next Close": self._next_close,
            "All sequences": self._all_seqeuences,
        }
        return attr_dict

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.hub.hub_id)},
            "name": f"{DOMAIN} {HUB}",
            "sw_version": 1,
            "model": "Normal",
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"

    async def async_make_strings(self, model: list[HourModel]) -> list[str]:
        ret = []
        for m in model:
            ret.append(await self.async_make_string(m))
        return ret

    async def async_make_string(self, model: HourModel) -> str:
        return f"{model.hour_start}-{model.hour_end} {model.price} {model.perkwh} {model.comparer}"
