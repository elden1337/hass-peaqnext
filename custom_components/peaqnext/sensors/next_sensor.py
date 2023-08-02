"""sensor implementation goes here"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..const import DOMAIN, HUB
from datetime import datetime, timedelta

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
        self._all_seqeuences: list[HourModel]|None = None
        self._consumption_type = None
        self._duration_in_minutes = None
        self._consumption_in_kwh = None
        self._non_hours_start = []
        self._non_hours_end = []
        self._closest_cheap_hour = None

    @property
    def state(self) -> float:
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:clock-start"

    async def async_update(self) -> None:
        status = await self.hub.async_get_updates(nametoid(self.given_name))
        self._all_seqeuences = self._make_dict(status.get("all_sequences", []))
        self._state = self._make_string(status["best_close_start"])
        self._consumption_type = status["consumption_type"]
        self._duration_in_minutes = status["duration_in_minutes"]
        self._consumption_in_kwh = status["consumption_in_kwh"]
        self._non_hours_start = status.get("non_hours_start", [])
        self._non_hours_end = status.get("non_hours_end", [])
        self._closest_cheap_hour = status.get("closest_cheap_hour", 12)

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "All sequences": self._all_seqeuences,
            "Consumption type": self._consumption_type,
            "Duration in minutes": self._duration_in_minutes,
            "Consumption in kWh": self._consumption_in_kwh,
            "Closest cheap hour limit": f"{self._closest_cheap_hour}h",
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

    def _make_dict(self, model: list[HourModel]) -> list[str]:
        ret = {}
        for m in model:
            ret[self._make_hours_display(m)] = self._make_price(m)
        return ret

    def _make_price(self, model: HourModel) -> str:
        return f"({model.price} {self.hub.nordpool.currency})"

    def _make_string(self, model: HourModel) -> str:
        return f"{self._make_hours_display(model)} {self._make_price(model)}"

    def _make_hours_display(self, model: HourModel) -> str:
        if model is None:
            return ""
        tomorrow1: str = ""
        tomorrow2: str = ""
        if model.dt_start.day > datetime.now().day:
            tomorrow1 = "⁺¹"
        if model.dt_end.day > datetime.now().day:
            tomorrow2 = "⁺¹"
        return f"{model.dt_start.hour}:00{tomorrow1}-{model.dt_end.hour}:{self._string_minute(self._duration_in_minutes, model.dt_start.hour)}{tomorrow2}"

    @staticmethod
    def _string_minute(dur_minutes: int, hour_start: int) -> str:
        try:
            dtstart = datetime(2023, 1, 1, hour_start, 0, 0)
            dtend = dtstart + timedelta(minutes=dur_minutes)
            ret = dtend.minute
            return f"{ret:02d}"
        except Exception as e:
            return "00"