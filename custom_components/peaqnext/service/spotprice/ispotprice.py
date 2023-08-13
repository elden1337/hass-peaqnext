import logging
import homeassistant.helpers.template as template
import asyncio
from custom_components.peaqnext.service.spotprice.spotprice_dto import ISpotPriceDTO
from custom_components.peaqnext.service.spotprice.const import *
from abc import abstractmethod

_LOGGER = logging.getLogger(__name__)


class ISpotPrice:
    def __init__(self, hub, source: str, test:bool = False):
        self._source: str = source
        _LOGGER.debug(f"Initializing Spotprice for {self._source}.")
        self.hub = hub
        print(f"Initializing Spotprice for {self._source}. {self.hub}.")
        self._entity: str | None = None
        self._is_initialized: bool = False
        self._currency: str = ""
        self._state: float = 0.0
        self._prices: list[float] = []
        self._prices_tomorrow: list[float] = []
        self._use_cent: bool = False
        if not test:
            self.state_machine = hub.state_machine
            self.setup()

    @property
    def entity(self) -> str:
        return getattr(self, "_entity", "")

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def state(self) -> float:
        return self._state

    @state.setter
    def state(self, val) -> None:
        if self._state != val:
            self._state = val

    @property
    def prices(self) -> list[float]:
        return self._prices

    @prices.setter
    def prices(self, val) -> None:
        self._prices = val

    @property
    def prices_tomorrow(self) -> list[float]:
        return self._prices_tomorrow

    @prices_tomorrow.setter
    def prices_tomorrow(self, val) -> None:
        self._prices_tomorrow = val

    @property
    def use_cent(self) -> bool:
        return self._use_cent

    @abstractmethod
    async def async_update_spotprice(self) -> None:
        pass

    @abstractmethod
    async def async_set_dto(self, ret) -> None:
        pass

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

    async def async_update_spotprice(self) -> None:
        if self.entity is not None:
            ret = self.state_machine.states.get(self.entity)
            if ret is not None:
                await self.async_set_dto(ret)
            else:
                _LOGGER.debug(
                    f"Could not get spot-prices. Entity: {self.entity}. Retrying..."
                )

    async def async_update_set_prices(self, result: ISpotPriceDTO) -> bool:
        ret = False
        if self.prices != result.today:
            self.prices = result.today
            ret = True
        if result.tomorrow_valid and result.tomorrow is not None:
            if self.prices_tomorrow != result.tomorrow:
                self.prices_tomorrow = result.tomorrow
                ret = True
        else:
            self.prices_tomorrow = []
            ret = True
        self._currency = result.currency
        self._use_cent = result.price_in_cent
        self.state = result.state
        return ret





