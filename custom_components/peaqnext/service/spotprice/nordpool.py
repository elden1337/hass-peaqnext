from custom_components.peaqnext.service.spotprice.ispotprice import ISpotPrice
from custom_components.peaqnext.service.spotprice.spotprice_dto import NordpoolDTO
from custom_components.peaqnext.service.spotprice.const import NORDPOOL
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)


class NordPoolUpdater(ISpotPrice):
    def __init__(self, hub, test: bool = False):
        super().__init__(hub=hub, source=NORDPOOL, test=test)

    async def async_set_dto(self, ret) -> None:
        _result = NordpoolDTO()
        await _result.set_model(ret)

        if await self.async_update_set_prices(_result):
            await self.hub.async_update_prices(
                (self.prices, self.prices_tomorrow)
            )
            self._is_initialized = True

    def setup(self):
        try:
            entities = [
                entity_id
                for entity_id in self.state_machine.states.async_entity_ids()
                if entity_id.startswith("sensor.nordpool")
            ]

            _LOGGER.debug(f"Found {list(entities)} Spotprice entities.")

            if len(entities) < 1:
                raise Exception("no entities found for Spotprice.")

            if len(entities) == 1:
                self._setup_set_entity(entities[0])

            else:
                _found: bool = False

                for e in entities:
                    if self._test_sensor(e):
                        _found = True
                        self._setup_set_entity(e)
                        break

                if not _found:
                    _LOGGER.error(
                        "more than one Spotprice entity found. Cannot continue."
                    )

        except Exception as e:
            _LOGGER.error(
                f"I was unable to get a Spotprice-entity. Cannot continue.: {e}"
            )

    def _setup_set_entity(self, entity: str) -> None:
        self._entity = entity

        _LOGGER.debug(
            f"Nordpool has been set up and is ready to be used with {self.entity}"
        )

        asyncio.run_coroutine_threadsafe(
            self.async_update_spotprice(),
            self.state_machine.loop,
        )

    def _test_sensor(self, sensor: str) -> bool:
        """
        Testing whether the sensor has a set value for
        additional_costs_current_hour.
        This is the only way we can differ when there are
        multiple sensors present.
        """

        state = self.state_machine.states.get(sensor)

        if state:
            attr = state.attributes.get(
                "additional_costs_current_hour",
                0
            )

            if attr != 0:
                return True

        return False
