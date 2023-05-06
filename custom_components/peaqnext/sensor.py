"""Platform for sensor integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.peaqnext.const import DOMAIN
from custom_components.peaqnext.sensors.next_sensor import PeaqNextSensor

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=4)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities
):
    """Add sensors for passed config_entry in HA."""

    hub = hass.data[DOMAIN]["hub"]
    hass.async_create_task(async_setup(hub, config, async_add_entities))


async def async_setup(hub, config, async_add_entities):
    sensors = []
    for s in config.data.get("sensors"):
        sensors.append(PeaqNextSensor(hub, config.entry_id, s["name"]))

    async_add_entities(sensors)
