import logging
from typing import Any
from custom_components.peaqnext.service.models.sensor_model import NextSensor
from custom_components.peaqnext.service.nordpool.nordpool import NordPoolUpdater
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change

_LOGGER = logging.getLogger(__name__)


class Hub:
    hub_id = 33512
    hubname = "PeaqNext"

    def __init__(self, hass) -> Any:
        self.state_machine: HomeAssistant = hass
        self.sensors: list[NextSensor] = []
        self.nordpool = NordPoolUpdater(self)
        self.sensors_dict: dict[str:NextSensor] = {}
        async_track_state_change(
            self.state_machine,
            [self.nordpool.nordpool_entity],
            self.async_state_changed,
        )

    async def async_setup(self, sensors: list[NextSensor]) -> None:
        self.sensors = sensors
        for s in self.sensors:
            self.sensors_dict[s.hass_entity_id] = s

    async def async_prices_changed(self, prices: list) -> None:
        for s in self.sensors:
            await s.async_update_sensor(prices)

    async def async_get_updates(self, sensor_id: str) -> dict:
        active_sensor = self.sensors_dict.get(sensor_id, None)
        if active_sensor is None:
            return {}
        return {
            "state": active_sensor.best_start,
            "best_close_start": active_sensor.best_close_start,
            "all_sequences": active_sensor.all_sequences,
        }

    @callback
    async def async_state_changed(self, entity_id, old_state, new_state):
        if entity_id is not None:
            try:
                if old_state is None or old_state != new_state:
                    await self.nordpool.async_update_nordpool()
            except Exception as e:
                msg = f"Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}"
                _LOGGER.error(msg)
