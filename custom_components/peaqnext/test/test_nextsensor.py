import pytest

from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.models.sensor_model import NextSensor
import custom_components.peaqnext.test.prices as _p
from datetime import date

@pytest.mark.asyncio
async def test_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10) 
    s.set_hour(2)   
    await s.async_update_sensor([_p.P230729BE,[]])    
    assert s.best_close_start.price == 0.12
    assert s.best_close_start.hour_start == 15    

@pytest.mark.asyncio
async def test_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10) 
    s.set_hour(2)   
    await s.async_update_sensor([[h*100 for h in _p.P230729BE],[]], use_cent=True)    
    assert s.best_close_start.hour_start == 15
    assert s.best_close_start.price == 0.12

@pytest.mark.asyncio
async def test_flat_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=1800, total_consumption_in_kwh=10) 
    s.set_hour(1)   
    await s.async_update_sensor([_p.PFLAT,[]])    
    assert s.best_close_start.hour_start == 1
    assert s.best_close_start.price == 10

@pytest.mark.asyncio
async def test_flat_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=1800, total_consumption_in_kwh=10) 
    s.set_hour(1)   
    await s.async_update_sensor([[p *100 for p in _p.PFLAT],[]],use_cent=True)
    assert s.best_close_start.hour_start == 1
    assert s.best_close_start.price == 10

@pytest.mark.asyncio
async def test_correct_sorting():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10) 
    s.set_hour(2)   
    await s.async_update_sensor([_p.P230729BE,[]])        
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: x.comparer)
    assert all_seq_copy == s.all_sequences


@pytest.mark.asyncio
async def test_correct_sorting_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10) 
    s.set_hour(2)   
    await s.async_update_sensor([[h*100 for h in _p.P230729BE],[]], use_cent=True)        
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: x.price)
    assert all_seq_copy == s.all_sequences

@pytest.mark.asyncio
async def test_correct_sorting_negative_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10) 
    s.set_hour(2)   
    await s.async_update_sensor([_p.PNEGATIVE,[]], use_cent=False)        
    # for h in s.all_sequences:
    #     print(h)
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: x.price)
    assert all_seq_copy == s.all_sequences
    

@pytest.mark.asyncio
async def test_correct_sorting_negative_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10) 
    s.set_hour(2)   
    await s.async_update_sensor([[h*100 for h in _p.PNEGATIVE],[]], use_cent=True)        
    # for h in s.all_sequences:
    #     print(h)
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: x.price)
    assert all_seq_copy == s.all_sequences


@pytest.mark.asyncio
async def test_start_nonhours():
    nh_start = [6,7,8]    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10,non_hours_start=nh_start) 
    s.set_hour(2)   
    await s.async_update_sensor([_p.P230729BE,[]], use_cent=False)        
    starts = [h.hour_start for h in s.all_sequences]
    assert all([h not in starts for h in nh_start])

@pytest.mark.asyncio
async def test_end_nonhours():
    nh_end = [6,7,8]    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10,non_hours_end=nh_end)
    s.set_hour(2)   
    await s.async_update_sensor([_p.P230729BE,[]], use_cent=False)        
    ends = [h.hour_end for h in s.all_sequences]
    assert all([h not in ends for h in nh_end])

@pytest.mark.asyncio
async def test_end_nonhours_washer():
    nh_end = [23, 0, 1, 2, 3, 4, 5]
    s = NextSensor(consumption_type=ConsumptionType.PeakOut, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=12000, total_consumption_in_kwh=1.2,non_hours_end=nh_end)
    s.set_hour(21)   
    s.set_date(date(2023,7,31))
    await s.async_update_sensor([_p.P230731,_p.P230801])        
    ends = [h.hour_end for h in s.all_sequences]
    for h in s.all_sequences:
        print(h.hour_start, h.hour_end, h.hour_end in nh_end)
    assert all([h not in ends for h in nh_end])
    #assert 1 > 2    

@pytest.mark.asyncio
async def test_start_and_end_nonhours():
    nh_end = [6,7,8]    
    nh_start = [12,13,14]
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=7200, total_consumption_in_kwh=10,non_hours_end=nh_end, non_hours_start=nh_start)
    s.set_hour(2)   
    await s.async_update_sensor([_p.P230729BE,[]], use_cent=False)        
    ends = [h.hour_end for h in s.all_sequences]
    starts = [h.hour_start for h in s.all_sequences]
    assert all([h not in ends for h in nh_end])
    assert all([h not in starts for h in nh_start])

@pytest.mark.asyncio
async def test_midnight():
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_seconds=3720, total_consumption_in_kwh=1.1)
    s.set_hour(0)
    s.set_date(date(2023,7,30))
    await s.async_update_sensor([_p.P230731,[]])
    assert len(s.all_sequences) == 23
    s.set_hour(13)
    await s.async_update_sensor([_p.P230731,_p.P230801])
    assert len(s.all_sequences) == 34
    s.set_date(date(2023,8,1))
    s.set_hour(0)
    await s.async_update_sensor([_p.P230801,[]])
    for h in sorted(s.all_sequences, key=lambda x: x.idx):
        print(h)
    assert len(s.all_sequences) == 23