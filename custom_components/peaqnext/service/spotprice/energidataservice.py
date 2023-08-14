from custom_components.peaqnext.service.spotprice.ispotprice import ISpotPrice
from custom_components.peaqnext.service.spotprice.spotprice_dto import EnergiDataServiceDTO
from custom_components.peaqnext.service.spotprice.const import ENERGIDATASERVICE, ENERGIDATASERVICE_SENSOR
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class EnergiDataServiceUpdater(ISpotPrice):
    def __init__(self, hub, test:bool = False):
        super().__init__(hub=hub, source=ENERGIDATASERVICE, test=test)

    async def async_set_dto(self, ret) -> None:
        _result = EnergiDataServiceDTO()
        await _result.set_model(ret)
        if await self.async_update_set_prices(_result):
            await self.hub.async_update_prices(
                (self.prices, self.prices_tomorrow)
            )
            self._is_initialized = True

    def setup(self):
        try:
            sensor = self.state_machine.states.get(ENERGIDATASERVICE_SENSOR)
            if not sensor.state:
                raise Exception("no entities found for Spotprice.")
            else:
                self._entity = ENERGIDATASERVICE_SENSOR
                _LOGGER.debug(
                    f"EnergiDataService has been set up and is ready to be used with {self.entity}"
                )
                asyncio.run_coroutine_threadsafe(
                    self.async_update_spotprice(),
                    self.state_machine.loop,
                )
        except Exception as e:
            _LOGGER.error(
                f"I was unable to get a Spotprice-entity. Cannot continue.: {e}"
            )