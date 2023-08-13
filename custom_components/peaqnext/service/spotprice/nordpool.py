from custom_components.peaqnext.service.spotprice.ispotprice import ISpotPrice
from custom_components.peaqnext.service.spotprice.spotprice_dto import NordpoolDTO
from custom_components.peaqnext.service.spotprice.const import NORDPOOL

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