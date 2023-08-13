from custom_components.peaqnext.service.spotprice.const import *
import homeassistant.helpers.template as template
from custom_components.peaqnext.service.spotprice.ispotprice import ISpotPrice
from custom_components.peaqnext.service.spotprice.nordpool import NordPoolUpdater
from custom_components.peaqnext.service.spotprice.energidataservice import EnergiDataServiceUpdater

class SpotPriceFactory:

    sources = {
        NORDPOOL: NordPoolUpdater,
        ENERGIDATASERVICE: EnergiDataServiceUpdater
    }

    @staticmethod
    def create(hub, test:bool = False) -> ISpotPrice:
        if test:
            return NordPoolUpdater(hub, test)
        source = SpotPriceFactory.test_connections(hub.state_machine)
        return SpotPriceFactory.sources[source](hub, test)

    @staticmethod
    def test_connections(hass) -> str:
        entities = template.integration_entities(hass, ENERGIDATASERVICE)            
        if len(list(entities)):
            ENERGIDATASERVICE
        return NORDPOOL
                

    