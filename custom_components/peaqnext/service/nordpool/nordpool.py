import logging
import homeassistant.helpers.template as template
import asyncio
from custom_components.peaqnext.service.nordpool.nordpool_dto import NordpoolDTO


_LOGGER = logging.getLogger(__name__)
NORDPOOL = "nordpool"


class NordPoolUpdater:
    def __init__(self, hub):
        self.hub = hub
        self.state_machine = hub.state_machine
        self._nordpool_entity: str | None = None
        self._is_initialized: bool = False
        self._currency: str = ""
        self._state: float = 0.0
        self._prices: list[float] = []
        self._prices_tomorrow: list[float] = []
        self._use_cent: bool = False
        self.setup()

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

    @property
    def nordpool_entity(self) -> str:
        return getattr(self, "_nordpool_entity", "")

    async def async_update_nordpool(self) -> None:
        if self.nordpool_entity is not None:
            ret = self.state_machine.states.get(self.nordpool_entity)
            _result = NordpoolDTO()
            if ret is not None:
                await _result.set_model(ret)
                if await self.async_update_set_prices(_result):
                    await self.hub.async_update_prices(
                        [self.prices, self.prices_tomorrow]
                    )
                    self._is_initialized = True
            elif self.hub.is_initialized:
                _LOGGER.debug(
                    f"Could not get nordpool-prices. Nordpool-entity: {self.nordpool_entity}"
                )

    async def async_update_set_prices(self, result: NordpoolDTO) -> bool:
        ret = False
        if self.prices != result.today:
            self.prices = result.today
            ret = True
        if result.tomorrow_valid:
            if self.prices_tomorrow != result.tomorrow:
                self.prices_tomorrow = result.tomorrow
                ret = True
        else:
            if self.prices_tomorrow:
                self.prices_tomorrow = []
                ret = True
        self._currency = result.currency
        self._use_cent = result.price_in_cent
        self.state = result.state
        return ret

    def setup(self):
        try:
            entities = template.integration_entities(self.state_machine, NORDPOOL)
            _LOGGER.debug(f"Found {list(entities)} Nordpool entities.")
            if len(list(entities)) < 1:
                raise Exception("no entities found for Nordpool.")
            if len(list(entities)) == 1:
                self._nordpool_entity = entities[0]
                _LOGGER.debug(
                    f"Nordpool has been set up and is ready to be used with {self.nordpool_entity}"
                )
                asyncio.run_coroutine_threadsafe(
                    self.async_update_nordpool(),
                    self.state_machine.loop,
                )
            else:
                _LOGGER.error(f"more than one Nordpool entity found. Cannot continue.")
        except Exception as e:
            _LOGGER.error(
                f"I was unable to get a Nordpool-entity. Cannot continue.: {e}"
            )
