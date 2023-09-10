"""The peaqev integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry  # pylint: disable=import-error
from homeassistant.helpers.device_registry import DeviceEntry  # pylint: disable=import-error
from homeassistant.core import HomeAssistant
from custom_components.peaqnext.service.models.next_sensor.enums.calculate_by import CalculateBy
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy
from custom_components.peaqnext.services import async_prepare_register_services  # pylint: disable=import-error
from custom_components.peaqnext.util import nametoid
from custom_components.peaqnext.service.hub import Hub
from custom_components.peaqnext.service.models.consumption_type import ConsumptionType
from custom_components.peaqnext.service.models.sensor_model import NextSensor
from .const import (CONF_CALCULATE_BY, CONF_CUSTOM_CONSUMPTION_PATTERN, CONF_DEDUCT_PRICE, CONF_UPDATE_BY, DOMAIN, PLATFORMS, HUB, CONF_NONHOURS_END, CONF_CONSUMPTION_TYPE, CONF_NAME, CONF_NONHOURS_START, CONF_SENSORS, CONF_TOTAL_CONSUMPTION_IN_KWH, CONF_TOTAL_DURATION_IN_MINUTES, CONF_CLOSEST_CHEAP)
from datetime import datetime
from uuid import uuid4

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][conf.entry_id] = conf.data
    hub = Hub(hass)
    hass.data[DOMAIN][HUB] = hub
    internal_sensors = await async_create_internal_sensors(conf)
    await hub.async_setup(internal_sensors)

    # conf.async_on_unload(conf.add_update_listener(async_update_entry))
    await async_prepare_register_services(hub, hass)

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(conf, platform)
        )

    return True

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""

async def async_create_internal_sensors(conf: ConfigEntry) -> list[NextSensor]:
    sensors = []
    for s in conf.data.get(CONF_SENSORS):
        sensors.append(
            NextSensor(
                consumption_type=ConsumptionType(s[CONF_CONSUMPTION_TYPE]),
                custom_consumption_pattern=s.get(CONF_CUSTOM_CONSUMPTION_PATTERN, None),
                name=s[CONF_NAME],
                hass_entity_id=nametoid(s[CONF_NAME]),
                total_duration_in_minutes=s[CONF_TOTAL_DURATION_IN_MINUTES],
                total_consumption_in_kwh=s[CONF_TOTAL_CONSUMPTION_IN_KWH],
                non_hours_start=s.get(CONF_NONHOURS_START, []),
                non_hours_end=s.get(CONF_NONHOURS_END, []),
                default_closest_cheap=s.get(CONF_CLOSEST_CHEAP, 12),
                deduct_price=s.get(CONF_DEDUCT_PRICE, 0),
                update_by=UpdateBy(s.get(CONF_UPDATE_BY)),
                calculate_by=CalculateBy(s.get(CONF_CALCULATE_BY)),
            )
        )
    return sensors


async def async_update_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload Peaqev component when options changed."""
    pass


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
