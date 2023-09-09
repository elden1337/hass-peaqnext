"""sensor implementation goes here"""
from __future__ import annotations
from typing import TYPE_CHECKING

from custom_components.peaqnext.service.models.consumption_type import ConsumptionType
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
        self._raw_start = None
        self._price_source: str|None = None
        self._non_hours_start = []
        self._non_hours_end = []
        self._closest_cheap_hour = None
        self._custom_consumption_pattern = []
        self._update_by = None
        self._calculate_by = None

    @property
    def state(self) -> float:
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:clock-start"

    async def async_update(self) -> None:
        status = None
        try:
            status = await self.hub.async_get_updates(nametoid(self.given_name))
            self._raw_start = self._set_raw_start(status["best_close_start"].dt_start)
            self._all_seqeuences = self._make_dict(status.get("all_sequences", []))
            self._state = self._make_string(status["best_close_start"])
            self._consumption_type = status["consumption_type"]
            self._duration_in_minutes = status["duration_in_minutes"]
            self._consumption_in_kwh = status["consumption_in_kwh"]
            self._non_hours_start = status.get("non_hours_start", [])
            self._non_hours_end = status.get("non_hours_end", [])
            self._closest_cheap_hour = status.get("closest_cheap_hour", 12)
            self._custom_consumption_pattern = status.get("custom_consumption_pattern", [])
            self._price_source = status.get("price_source", "unknown").capitalize()
            self._update_by = status.get("update_by", "unknown").capitalize()
            self._calculate_by = status.get("calculate_by", "unknown").capitalize()
        except Exception as e:
            _LOGGER.debug(f"status for {self.given_name}: {status}. Exception: {e}")
            pass

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
        if self._consumption_type == ConsumptionType.Custom.value:
            attr_dict["Custom consumption pattern"] = self._custom_consumption_pattern
        attr_dict["raw_start"]= self._raw_start
        attr_dict["price_source"] = self._price_source
        attr_dict["update_by"] = self._update_by
        attr_dict["calculate_by"] = self._calculate_by
        return attr_dict

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.hub.hub_id)},
            "name": f"{DOMAIN} {HUB} ({self.hub.hub_id})",
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
        if model is None:
            return ""
        return f"({model.price} {self.hub.spotprice.currency})"

    def _make_string(self, model: HourModel) -> str:
        if not self._check_hourmodel(model):
            return ""
        return f"{self._make_hours_display(model)} {self._make_price(model)}"

    @staticmethod
    def _set_raw_start(start: datetime) -> str:
        return start.strftime("%Y-%m-%dT%H:%M:%S.%f")

    def _check_hourmodel(self, model: HourModel) -> bool:
        if model is None:
            _LOGGER.debug(f"model is None {self.name}")
            return False
        elif not model.is_valid:
            _LOGGER.debug(f"model is invalid {self.name}. Model: {model}")
            return False
        return True

    @staticmethod
    def _get_tomorrow_assignation(comparer: bool) -> str:
        return "⁺¹" if comparer else ""

    @staticmethod
    def _add_now_to_date(model: HourModel) -> str:
        return ">> " if model.dt_start.day == datetime.now().day and model.dt_start.hour == datetime.now().hour else ""

    def _make_hours_display(self, model: HourModel) -> str:
        if not self._check_hourmodel(model):
            return ""
        tomorrow1: str = self._get_tomorrow_assignation(model.dt_start.day > datetime.now().day)
        tomorrow2: str = self._get_tomorrow_assignation(model.dt_end.day > datetime.now().day)
        ret = f"{model.dt_start.strftime('%H:%M')}{tomorrow1}-{model.dt_end.strftime('%H:%M')}{tomorrow2}"
        return f"{self._add_now_to_date(model)}{ret}"
        