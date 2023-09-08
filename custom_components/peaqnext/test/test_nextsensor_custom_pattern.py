from statistics import mean
import pytest
from custom_components.peaqnext.service.hours import cheapest_hour
from custom_components.peaqnext.service.hub import Hub
from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.models.hour_model import HourModel
from custom_components.peaqnext.service.models.sensor_model import NextSensor
import custom_components.peaqnext.test.prices as _p
from datetime import date, datetime, timedelta

class MockNordpool:
    def __init__(self, state:float=0, today:list=[], tomorrow:list=[], average:float=0, currency:str="", price_in_cent:bool=False, tomorrow_valid:bool=False) -> None:
        self.state = state
        self.attributes = {
            "today": today,
            "tomorrow": tomorrow,
            "tomorrow_valid": tomorrow_valid,
            "average": average,
            "currency": currency,
            "price_in_cent": price_in_cent,
        }

@pytest.mark.asyncio
async def test_override_consumption():    
    s = NextSensor(consumption_type=ConsumptionType.Custom, custom_consumption_pattern="1.2, 3, 4, 6, 8",name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(4)   
    await s.async_update_sensor((_p.P230729BE,[]))   
    print(s.all_sequences)
    assert s.all_sequences[0].sum_consumption_pattern == 10
    await s.async_override_sensor_data(total_consumption_in_kwh=20)
    assert s.all_sequences[0].sum_consumption_pattern == 20
    await s.async_override_sensor_data(total_consumption_in_kwh=200)
    assert s.all_sequences[0].sum_consumption_pattern == 200
    
