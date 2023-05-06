"""The peaqev integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry  # pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pylint: disable=import-error
from custom_components.peaqnext.util import nametoid
from custom_components.peaqnext.service.hub import Hub
from custom_components.peaqnext.service.models.sensor_model import NextSensor

from .const import DOMAIN, PLATFORMS, HUB

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][conf.entry_id] = conf.data
    hub = Hub(hass)
    hass.data[DOMAIN][HUB] = hub
    internal_sensors = await async_create_internal_sensors(conf)
    await hub.async_setup(internal_sensors)

    # conf.async_on_unload(conf.add_update_listener(async_update_entry))
    # await async_prepare_register_services(hub, hass)

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(conf, platform)
        )

    return True


async def async_create_internal_sensors(conf: ConfigEntry) -> list[NextSensor]:
    sensors = []
    for s in conf.get("sensors"):
        sensors.append(
            NextSensor(
                consumption_type=s["consumption_type"],
                name=s["name"],
                hass_entity_id=nametoid(s["name"]),
                total_duration_in_seconds=s["total_duration_in_minutes"] * 60,
                total_consumption_in_kwh=s["total_consumption_in_kwh"],
            )
        )
    return sensors


async def async_update_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload Peaqev component when options changed."""
    pass


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
