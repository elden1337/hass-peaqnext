import logging
import time
from typing import Any, Dict
from datetime import datetime
from custom_components.peaqnext.service.models.sensor_model import NextSensor
from custom_components.peaqnext.service.spotprice.ispotprice import ISpotPrice
from custom_components.peaqnext.service.spotprice.spotprice_factory import SpotPriceFactory
from homeassistant.core import HomeAssistant, callback, Event, EventStateChangedData
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)
SPOTPRICE_UPDATE_FORCE = 60


class Hub:
    hub_id = 33512
    hubname = "PeaqNext"
    sensors_dict: Dict[str,NextSensor] = {}
    sensors: list[NextSensor] = []
    
    def __init__(self, hass, test:bool = False) -> None:
        if not test:
            self.state_machine: HomeAssistant = hass
        self._current_minute: int = None
        self.prices: tuple[list,list] = ([], [])
        self.spotprice: ISpotPrice = SpotPriceFactory.create(self, test)
        self.latest_spotprice_update = 0
        if not test:
            async_track_state_change_event(
                self.state_machine,
                [self.spotprice.entity],
                self._async_on_change,
            )

    async def async_setup(self, sensors: list[NextSensor]) -> None:
        self.sensors.extend(sensors)
        for s in self.sensors:
            self.sensors_dict[s.hass_entity_id] = s

    async def async_update_prices(self, prices: tuple[list,list]) -> None:
        self.prices = prices
        for s in self.sensors:
            try:
                await s.async_update_sensor(prices, self.spotprice.use_cent, self.spotprice.currency)
            except Exception as e:
                _LOGGER.error(
                    f"Unable to update sensor: {s.hass_entity_id}. Exception: {e}"
                )

    async def async_get_updates(self, sensor_id: str) -> dict:
        if time.time() - self.latest_spotprice_update > SPOTPRICE_UPDATE_FORCE:
            await self.spotprice.async_update_spotprice()
            self.latest_spotprice_update = time.time()
            await self.async_update_prices(
                (self.spotprice.prices, self.spotprice.prices_tomorrow)
            )
        active_sensor: NextSensor = self.sensors_dict.get(sensor_id, None)
        return await self.async_get_sensor_updates(active_sensor)

    async def async_get_sensor_updates(self, active_sensor: NextSensor) -> dict:
        if active_sensor is None:
            return {}
        await self.async_update_prices(self.prices)
        return {
            "state": active_sensor.best_start,
            "best_close_start": active_sensor.best_close_start,
            "all_sequences": active_sensor.all_sequences,
            "consumption_type": active_sensor.consumption_type.value,
            "duration_in_minutes": active_sensor.total_duration_in_seconds / 60,
            "consumption_in_kwh": active_sensor.total_consumption_in_kwh,
            "non_hours_start": active_sensor.non_hours_start,
            "non_hours_end": active_sensor.non_hours_end,
            "closest_cheap_hour": active_sensor.default_closest_cheap,
            "custom_consumption_pattern": active_sensor.custom_consumption_pattern_list,
            "price_source": self.spotprice.source,
            "update_by": active_sensor.update_by,
            "calculate_by": active_sensor.calculate_by,
            "relative_time": active_sensor.show_relative_time,
        }

    @callback
    async def _async_on_change(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data['entity_id']
        old_state = event.data['old_state']
        new_state = event.data['new_state']
        if entity_id is not None:
            try:
                if old_state is None or old_state != new_state:
                    await self.spotprice.async_update_spotprice()
            except Exception as e:
                msg = f"Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}"
                _LOGGER.error(msg)
