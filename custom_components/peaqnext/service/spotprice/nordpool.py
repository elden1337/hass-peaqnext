from custom_components.peaqnext.service.spotprice.ispotprice import ISpotPrice
from custom_components.peaqnext.service.spotprice.spotprice_dto import NordpoolDTO
from custom_components.peaqnext.service.spotprice.const import NORDPOOL
import logging
import asyncio
import homeassistant.helpers.template as template
_LOGGER = logging.getLogger(__name__)


class NordPoolUpdater(ISpotPrice):
    def __init__(self, hub, test:bool = False):
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
            entities = template.integration_entities(self.state_machine, self._source)
            _LOGGER.debug(f"Found {list(entities)} Spotprice entities.")
            if len(list(entities)) < 1:
                raise Exception("no entities found for Spotprice.")
            if len(list(entities)) == 1:
                self._entity = entities[0]
                _LOGGER.debug(
                    f"Nordpool has been set up and is ready to be used with {self.entity}"
                )
                asyncio.run_coroutine_threadsafe(
                    self.async_update_spotprice(),
                    self.state_machine.loop,
                )
            else:
                _LOGGER.error(f"more than one Spotprice entity found. Cannot continue.")
        except Exception as e:
            _LOGGER.error(
                f"I was unable to get a Spotprice-entity. Cannot continue.: {e}"
            )