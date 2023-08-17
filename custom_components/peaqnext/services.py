from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqnext.service.hub import Hub
    from homeassistant.core import HomeAssistant  # pylint: disable=import-error

import logging

from custom_components.peaqnext.service.models.sensor_model import NextSensor
from enum import Enum
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ServiceCalls(Enum):
    OVERRIDE_SENSOR_DATA = "override_sensor_data"
    CANCEL_OVERRIDE = "cancel_override"


async def async_prepare_register_services(hub: Hub, hass: HomeAssistant) -> None:
    def _parse_sensor_id(sensor_id: str) -> NextSensor|None:
        if not sensor_id.startswith("sensor.peaqnext_"):
            if sensor_id.startswith("peaqnext_"):
                sensor_id = "sensor." + sensor_id
            else:
                sensor_id = "sensor.peaqnext_" + sensor_id
        return hub.sensors_dict.get(sensor_id, None)
        
    async def async_servicehandler_override_sensor_data(call):
        _sensor = _parse_sensor_id(call.data.get("sensor_entity", None))
        if _sensor:
            _LOGGER.debug("Calling {} service".format(ServiceCalls.OVERRIDE_SENSOR_DATA.value))
            await _sensor.async_override_sensor_data(
                total_consumption_in_kwh=all.data.get("consumption_in_kwh", None), 
                total_duration_in_minutes=call.data.get("duration_in_minutes", None), 
                custom_consumption_pattern=call.data.get("custom_consumption_pattern", None),
                non_hours_start=call.data.get("non_hours_start", None),
                non_hours_end=call.data.get("non_hours_end", None),
                timeout=call.data.get("timeout", None)
                )
        else:
            _LOGGER.error("Unable to parse sensor id for service call: {}".format(ServiceCalls.OVERRIDE_SENSOR_DATA.value))
    
    async def async_servicehandler_cancel_override(call):
        _sensor = _parse_sensor_id(call.data.get("sensor_entity", None))
        if _sensor:
            _LOGGER.debug("Calling {} service".format(ServiceCalls.CANCEL_OVERRIDE.value))
            await _sensor.async_cancel_override()
        else:
            _LOGGER.error("Unable to parse sensor id for service call: {}".format(ServiceCalls.CANCEL_OVERRIDE.value))
        
    # Register services
    SERVICES = {
        ServiceCalls.OVERRIDE_SENSOR_DATA: async_servicehandler_override_sensor_data,
        ServiceCalls.CANCEL_OVERRIDE: async_servicehandler_cancel_override
    }

    for service, handler in SERVICES.items():
        hass.services.async_register(DOMAIN, service.value, handler)
    _LOGGER.debug("Registered services: {}".format(SERVICES.keys()))
