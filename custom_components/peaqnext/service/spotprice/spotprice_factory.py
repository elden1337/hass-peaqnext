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
    def create(hass, test:bool = False) -> ISpotPrice:
        if test:
            raise Exception
        source = SpotPriceFactory.test_connections(hass)
        return SpotPriceFactory.sources[source](hass, test)

    @staticmethod
    def test_connections(hass) -> str:
        entities = template.integration_entities(hass, ENERGIDATASERVICE)            
        if len(list(entities)):
            ENERGIDATASERVICE
        return NORDPOOL
                

    