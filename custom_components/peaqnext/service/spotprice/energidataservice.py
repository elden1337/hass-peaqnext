from custom_components.peaqnext.service.spotprice.ispotprice import ISpotPrice
from custom_components.peaqnext.service.spotprice.spotprice_dto import EnergiDataServiceDTO

class EnergiDataServiceUpdater(ISpotPrice):
    def __init__(self, hub, ENERGIDATASERVICE, test:bool = False):
        super().__init__(hub, ENERGIDATASERVICE, test)

    async def async_set_dto(self, ret) -> None:
        _result = EnergiDataServiceDTO()
        await _result.set_model(ret)
        if await self.async_update_set_prices(_result):
            await self.hub.async_update_prices(
                (self.prices, self.prices_tomorrow)
            )
            self._is_initialized = True