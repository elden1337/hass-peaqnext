import pytest

from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.models.sensor_model import NextSensor
import custom_components.peaqnext.test.prices as _p

@pytest.mark.asyncio
async def test_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10) 
    s.set_hour(2)   
    await s.async_update_sensor([_p.P230729BE,[]])    
    assert s.best_close_start.price == 0.49
    assert s.best_close_start.hour_start == 12

@pytest.mark.asyncio
async def test_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10, use_cent=True) 
    s.set_hour(2)   
    await s.async_update_sensor([[h*100 for h in _p.P230729BE],[]])
    for sp in s.all_sequences:
        print(sp)
    # print(f"best close: {s.best_close_start}")
    assert s.best_close_start.hour_start == 12
    assert s.best_close_start.price == 0.49

@pytest.mark.asyncio
async def test_flat_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=1800, total_consumption_in_kwh=10, use_cent=False) 
    s.set_hour(1)   
    await s.async_update_sensor([_p.PFLAT,[]])    
    assert s.best_close_start.hour_start == 1
    assert s.best_close_start.price == 10

@pytest.mark.asyncio
async def test_flat_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=1800, total_consumption_in_kwh=10, use_cent=True) 
    s.set_hour(1)   
    await s.async_update_sensor([[p *100 for p in _p.PFLAT],[]])
    assert s.best_close_start.hour_start == 1
    assert s.best_close_start.price == 10