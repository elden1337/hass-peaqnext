import logging
import time
from typing import Any
from custom_components.peaqnext.service.models.sensor_model import NextSensor
from custom_components.peaqnext.service.nordpool.nordpool import NordPoolUpdater
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change

_LOGGER = logging.getLogger(__name__)
NORDPOOL_UPDATE_FORCE = 60


class Hub:
    hub_id = 33512
    hubname = "PeaqNext"

    def __init__(self, hass) -> Any:
        self.state_machine: HomeAssistant = hass
        self.sensors: list[NextSensor] = []
        self.nordpool = NordPoolUpdater(self)
        self.latest_nordpool_update = 0
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

    async def async_update_prices(self, prices: list) -> None:
        for s in self.sensors:
            try:
                await s.async_update_sensor(prices)
            except Exception as e:
                _LOGGER.error(
                    f"Unable to update sensor: {s.hass_entity_id}. Exception: {e}"
                )

    async def async_get_updates(self, sensor_id: str) -> dict:
        if time.time() - self.latest_nordpool_update > NORDPOOL_UPDATE_FORCE:
            await self.nordpool.async_update_nordpool()
            self.latest_nordpool_update = time.time()
            await self.async_update_prices(
                [self.nordpool.prices, self.nordpool.prices_tomorrow]
            )
        active_sensor = self.sensors_dict.get(sensor_id, None)
        if active_sensor is None:
            return {}
        return {
            "state": active_sensor.best_start,
            "best_close_start": active_sensor.best_close_start,
            "all_sequences": active_sensor.all_sequences,
            "consumption_type": active_sensor.consumption_type.value,
            "duration_in_minutes": active_sensor.total_duration_in_seconds / 60,
            "consumption_in_kwh": active_sensor.total_consumption_in_kwh,
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
