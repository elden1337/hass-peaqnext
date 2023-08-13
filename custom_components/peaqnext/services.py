# from __future__ import annotations

# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
#     from homeassistant.core import HomeAssistant  # pylint: disable=import-error

# import logging
# from enum import Enum

# from .const import DOMAIN

# _LOGGER = logging.getLogger(__name__)


# class ServiceCalls(Enum):
#     OVERRIDE_SENSOR_DATA = "override_sensor_data"

# async def async_servicehandler_override_sensor_data(call):
#     _sensor = call.data.get("sensor_entity", None)
#     _duration = call.data.get("cycle_duration_in_minutes", None)
#     _energy = call.data.get("cycle_energy_in_kwh", None)
    
#     _LOGGER.debug("Calling {} service".format(ServiceCalls.OVERRIDE_CHARGE_AMOUNT.value))
#     # if _amount and _amount > 0:
#     #     await hub.max_min_controller.async_servicecall_override_charge_amount(_amount)

#     # Register services
#     SERVICES = {
#         ServiceCalls.OVERRIDE_SENSOR_DATA: async_servicehandler_override_sensor_data
#     }

#     for service, handler in SERVICES.items():
#         hass.services.async_register(DOMAIN, service.value, handler)
#     _LOGGER.debug("Registered services: {}".format(SERVICES.keys()))
