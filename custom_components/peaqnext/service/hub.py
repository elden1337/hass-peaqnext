from typing import Any
from custom_components.peaqnext.service.models.sensor_model import NextSensor
from custom_components.peaqnext.service.nordpool.nordpool import NordPoolUpdater


class Hub:
    hub_id = 33512
    hubname = "PeaqNext"

    def __init__(self, hass) -> Any:
        self.state_machine = hass
        self.sensors: list[NextSensor] = []
        self.nordpool = NordPoolUpdater(self)
        self.sensors_dict: dict[str:NextSensor] = {}
        self.nordpool.setup()

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
            "best_start": active_sensor.best_start,
            "best_close_start": active_sensor.best_close_start,
            "all_sequences": active_sensor.all_sequences,
        }

    # @callback
    # async def async_state_change(
    #     self, entity_id: str, old_state: Any, new_state: Any
    # ) -> None:
    #     if old_state is None or new_state is None:
    #         return
    #     if old_state.state != new_state.state:
    #         await self.async_get_updates(entity_id)
