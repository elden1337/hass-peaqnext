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
        self._consumption_type = None
        self._duration_in_minutes = None
        self._consumption_in_kwh = None
        self._end_minute = None
        self._non_hours_start = []
        self._non_hours_end = []

    @property
    def state(self) -> float:
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:clock-start"

    async def async_update(self) -> None:
        status = await self.hub.async_get_updates(nametoid(self.given_name))
        self._all_seqeuences = await self.async_make_dict(status["all_sequences"])
        self._state = await self.async_make_string(status["best_close_start"])
        self._consumption_type = status["consumption_type"]
        self._duration_in_minutes = status["duration_in_minutes"]
        self._consumption_in_kwh = status["consumption_in_kwh"]
        self._non_hours_start = status["non_hours_start"]
        self._non_hours_end = status["non_hours_end"]
        self._end_minute = status["end_minute"]

    @property
    def extra_state_attributes(self) -> dict:
        # todo: fix attr for persisting the consumption-dict and connected-at
        attr_dict = {
            "All sequences": self._all_seqeuences,
            "Consumption type": self._consumption_type,
            "Duration in minutes": self._duration_in_minutes,
            "Consumption in kWh": self._consumption_in_kwh,
        }
        if len(self._non_hours_start) > 0:
            attr_dict["Non hours start"] = self._non_hours_start
        if len(self._non_hours_end) > 0:
            attr_dict["Non hours end"] = self._non_hours_end
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

    async def async_make_dict(self, model: list[HourModel]) -> list[str]:
        ret = {}
        for m in model:
            ret[await self.async_make_hours_display(m)] = await self.async_make_price(m)
        return ret

    async def async_make_price(self, model: HourModel) -> str:
        return f"({model.price} {self.hub.nordpool.currency})"

    async def async_make_string(self, model: HourModel) -> str:
        hours = await self.async_make_hours_display(model)
        price = await self.async_make_price(model)
        return f"{hours} {price}"

    async def async_string_minute(self, num_minute: int) -> str:
        if num_minute < 10:
            return f"0{num_minute}"
        return str(num_minute)

    async def async_make_hours_display(self, model: HourModel) -> str:
        tomorrow1: str = ""
        tomorrow2: str = ""
        if model.idx > 23:
            tomorrow1 = "⁺¹"
            tomorrow2 = "⁺¹"
        elif model.hour_end < model.hour_start:
            tomorrow2 = "⁺¹"
        return f"{model.hour_start}:00{tomorrow1}-{model.hour_end}:{await self.async_string_minute(self._end_minute)}{tomorrow2}"
