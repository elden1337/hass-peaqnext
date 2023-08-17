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
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(4)   
    await s.async_update_sensor((_p.P230729BE,[]))   
    assert s.total_consumption_in_kwh == 10
    await s.async_override_sensor_data(total_consumption_in_kwh=20)
    assert s.total_consumption_in_kwh == 20

@pytest.mark.asyncio
async def test_override_duration():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(4)   
    await s.async_update_sensor((_p.P230729BE,[]))   
    assert s.total_duration_in_seconds == 7200
    await s.async_override_sensor_data(total_duration_in_minutes=20)
    assert s.total_duration_in_seconds == 1200


@pytest.mark.asyncio
async def test_override_duration_reset():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(4)   
    await s.async_update_sensor((_p.P230729BE,[]))   
    assert s.total_duration_in_seconds == 7200
    await s.async_override_sensor_data(total_duration_in_minutes=20)
    assert s.total_duration_in_seconds == 1200
    # s.override_model.override = False
    await s.async_cancel_override()
    assert s.total_duration_in_seconds == 7200

@pytest.mark.asyncio
async def test_override_timeout_int():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(4)   
    await s.async_update_sensor((_p.P230729BE,[]))   
    assert s.total_duration_in_seconds == 7200
    await s.async_override_sensor_data(timeout=4, total_duration_in_minutes=20)
    assert s.override is True
    assert s.total_duration_in_seconds == 1200
    s.dt_model.set_hour(11)
    assert s.override is False
    #assert s.override_model.parsed_timeout == _now + timedelta(hours=10)