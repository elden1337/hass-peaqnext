from statistics import mean
import pytest
from custom_components.peaqnext.service.hours import cheapest_hour
from custom_components.peaqnext.service.hub import Hub
from custom_components.peaqnext.service.models.consumption_type import (
    ConsumptionType,
)
from custom_components.peaqnext.service.models.period_model import PeriodModel
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy
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
async def test_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(4)   
    await s.async_update_sensor((_p.P230729BE,[]))   
    assert s.best_close_start.price == 0.12
    assert s.best_close_start.dt_start.hour == 15    

@pytest.mark.asyncio
async def test_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(4)  
    await s.async_update_sensor(([h*100 for h in _p.P230729BE],[]), use_cent=True)    
    print(s.best_close_start)
    assert s.best_close_start.dt_start.hour == 15
    assert s.best_close_start.price == 0.12

@pytest.mark.asyncio
async def test_flat_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=30, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(1)   
    await s.async_update_sensor((_p.PFLAT,[]))    
    assert s.best_close_start.dt_start.hour == 1
    assert s.best_close_start.price == 10

@pytest.mark.asyncio
async def test_flat_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=30, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(1)   
    await s.async_update_sensor(([p *100 for p in _p.PFLAT],[]),use_cent=True)
    assert s.best_close_start.dt_start.hour == 1
    assert s.best_close_start.price == 10

@pytest.mark.asyncio
async def test_correct_sorting():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(2)   
    await s.async_update_sensor((_p.P230729BE,[]))        
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: (x.comparer, x.dt_start))
    assert all_seq_copy == s.all_sequences


@pytest.mark.asyncio
async def test_correct_sorting_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(2)   
    await s.async_update_sensor(([h*100 for h in _p.P230729BE],[]), use_cent=True)        
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: (x.comparer, x.dt_start))
    assert all_seq_copy == s.all_sequences

@pytest.mark.asyncio
async def test_correct_sorting_negative_prices():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(2)   
    await s.async_update_sensor((_p.PNEGATIVE,[]), use_cent=False)        
    # for h in s.all_sequences:
    #     print(h)
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: (x.comparer, x.dt_start))
    assert all_seq_copy == s.all_sequences
    

@pytest.mark.asyncio
async def test_correct_sorting_negative_prices_use_cent():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(2)           
    await s.async_update_sensor(([h*100 for h in _p.PNEGATIVE],[]), use_cent=False)
    # for h in s.all_sequences:
    #     print(h)
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: (x.comparer, x.dt_start))
    assert all_seq_copy == s.all_sequences


@pytest.mark.asyncio
async def test_start_nonhours():
    nh_start = [6,7,8]    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10,non_hours_start=nh_start) 
    s.dt_model.set_hour(2)   
    await s.async_update_sensor((_p.P230729BE,[]), use_cent=False)        
    starts = [h.dt_start.hour for h in s.all_sequences]
    assert all([h not in starts for h in nh_start])

@pytest.mark.asyncio
async def test_end_nonhours():
    nh_end = [6,7,8]    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10,non_hours_end=nh_end)
    s.dt_model.set_hour(2)   
    await s.async_update_sensor((_p.P230729BE,[]), use_cent=False)        
    ends = [h.dt_end.hour for h in s.all_sequences]
    assert all([h not in ends for h in nh_end])

@pytest.mark.asyncio
async def test_end_nonhours_washer():
    nh_end = [23, 0, 1, 2, 3, 4, 5]
    s = NextSensor(consumption_type=ConsumptionType.PeakOut, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=200, total_consumption_in_kwh=1.2,non_hours_end=nh_end)
    s.dt_model.set_hour(21)   
    s.dt_model.set_date(date(2023,7,31))
    await s.async_update_sensor((_p.P230731,_p.P230801))        
    ends = [h.dt_end.hour for h in s.all_sequences]
    assert all([h not in ends for h in nh_end])
    #assert 1 > 2    

@pytest.mark.asyncio
async def test_start_and_end_nonhours():
    nh_end = [6,7,8]    
    nh_start = [12,13,14]
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10,non_hours_end=nh_end, non_hours_start=nh_start)
    s.dt_model.set_hour(2)   
    await s.async_update_sensor((_p.P230729BE,[]), use_cent=False)        
    ends = [h.dt_end.hour for h in s.all_sequences]
    starts = [h.dt_start.hour for h in s.all_sequences]
    assert all([h not in ends for h in nh_end])
    assert all([h not in starts for h in nh_start])

@pytest.mark.asyncio
async def test_price_deduction():
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=60, total_consumption_in_kwh=1, deduct_price=0.5)
    s.dt_model.set_hour(2)   
    await s.async_update_sensor((_p.PFLAT,[]), use_cent=False)        
    assert s.best_close_start.price == 0.5

@pytest.mark.asyncio
async def test_midnight():
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
    s.dt_model.set_hour(0)
    s.dt_model.set_date(date(2023,7,30))
    await s.async_update_sensor((_p.P230731,[]))
    assert len(s.all_sequences) == 23
    s.dt_model.set_hour(13)
    print(s.dt_model.get_dt_now())
    await s.async_update_sensor((_p.P230731,_p.P230801))
    for a in s.all_sequences:
        print(a)
    assert len(s.all_sequences) == 34
    s.dt_model.set_date(date(2023,8,1))
    s.dt_model.set_hour(0)
    await s.async_update_sensor((_p.P230801,[]))
    assert len(s.all_sequences) == 23


@pytest.mark.asyncio
async def test_cheapest_hour():
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
    s.dt_model.set_date(date(2023,7,30))
    s.dt_model.set_hour(20)
    await s.async_update_sensor([_p.P230731,_p.P230801])
    tt = cheapest_hour(s.all_sequences, cheapest_cap=None, mock_dt=s.dt_model.get_dt_now())
    

@pytest.mark.asyncio
async def test_midnight_with_nordpool():
    hub = Hub(None, test=True)
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
    s.dt_model.set_hour(0)
    s.dt_model.set_date(date(2023,7,30))
    await hub.async_setup([s])
    np1 = MockNordpool(today=_p.P230731, tomorrow=[], average=mean(_p.P230731), currency="SEK", price_in_cent=False, tomorrow_valid=False)
    await hub.spotprice.async_set_dto(np1)    
    assert len(s.all_sequences) == 23
    s.dt_model.set_hour(13)
    np2 = MockNordpool(today=_p.P230731, tomorrow=_p.P230801, average=mean(_p.P230731), currency="SEK", price_in_cent=False, tomorrow_valid=True)
    await hub.spotprice.async_set_dto(np2)
    assert len(s.all_sequences) == 34
    s.dt_model.set_date(date(2023,8,1))
    s.dt_model.set_hour(0)
    np3 = MockNordpool(today=_p.P230801, tomorrow=None, average=mean(_p.P230801), currency="SEK", price_in_cent=False, tomorrow_valid=False)
    await hub.spotprice.async_set_dto(np3)
    assert len(s.all_sequences) == 23



@pytest.mark.asyncio
async def test_hub_updates_sensor():
    hub = Hub(None, test=True)
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
    s.dt_model.set_hour(0)
    s.dt_model.set_date(date(2023,7,30))
    await hub.async_setup([s])
    np1 = MockNordpool(today=_p.P230731, tomorrow=[], average=mean(_p.P230731), currency="SEK", price_in_cent=False, tomorrow_valid=False)
    await hub.spotprice.async_set_dto(np1)    
    assert len(s.all_sequences) == 23
    s.dt_model.set_hour(13)
    np2 = MockNordpool(today=_p.P230731, tomorrow=_p.P230801, average=mean(_p.P230731), currency="SEK", price_in_cent=False, tomorrow_valid=True)
    await hub.spotprice.async_set_dto(np2)
    tt = await hub.async_get_sensor_updates(s)
    s.dt_model.set_hour(19)
    tt2 = await hub.async_get_sensor_updates(s)
    assert tt2.get("best_close_start") != tt.get("best_close_start")

@pytest.mark.asyncio
async def test_hub_updates_sensor_2():
    hub = Hub(None, test=True)
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
    s.dt_model.set_hour(0)
    s.dt_model.set_date(date(2023,7,30))
    await hub.async_setup([s])
    np1 = MockNordpool(today=_p.P230731, tomorrow=[], average=mean(_p.P230731), currency="EUR", price_in_cent=False, tomorrow_valid=False)
    await hub.spotprice.async_set_dto(np1)    
    assert len(s.all_sequences) == 23
    s.dt_model.set_hour(13)
    np2 = MockNordpool(today=_p.P230731, tomorrow=_p.P230801, average=mean(_p.P230731), currency="EUR", price_in_cent=False, tomorrow_valid=True)
    await hub.spotprice.async_set_dto(np2)
    tt = await hub.async_get_sensor_updates(s)
    #print(f"best: {tt.get('best_close_start')}")
    s.dt_model.set_hour(19)
    tt2 = await hub.async_get_sensor_updates(s)
    #print(f"best: {tt2.get('best_close_start')}")
    ttt = tt.get("all_sequences")
    # for t in ttt:
    #     print(t.dt_start, t.dt_end, t.price)
    # assert 1 > 2


@pytest.mark.asyncio
async def test_hub_rounding_sek():
    hub = Hub(None, test=True)
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
    s.dt_model.set_hour(0)
    s.dt_model.set_date(date(2023,7,30))
    await hub.async_setup([s])
    np1 = MockNordpool(today=_p.P230729BE, tomorrow=[], average=mean(_p.P230729BE), currency="SEK", price_in_cent=False, tomorrow_valid=False)
    await hub.spotprice.async_set_dto(np1)    
    tt = await hub.async_get_sensor_updates(s)
    comparers = [t.comparer for t in tt.get("all_sequences")]
    assert all([len(str(c).split('.')[1]) <= 1 for c in comparers])

@pytest.mark.asyncio
async def test_hub_rounding_eur():
    hub = Hub(None, test=True)
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
    s.dt_model.set_hour(0)
    s.dt_model.set_date(date(2023,7,30))
    await hub.async_setup([s])
    np1 = MockNordpool(today=_p.P230729BE, tomorrow=[], average=mean(_p.P230729BE), currency="EUR", price_in_cent=False, tomorrow_valid=False)
    await hub.spotprice.async_set_dto(np1)    
    tt = await hub.async_get_sensor_updates(s)
    comparers = [t.comparer for t in tt.get("all_sequences")]
    for t in comparers:
        print(t)
    assert all([len(str(c).split('.')[1]) <= 2 for c in comparers])
    assert any([len(str(c).split('.')[1]) > 1 for c in comparers])


# @pytest.mark.asyncio
# async def test_hub_this_hour_visible():
#     hub = Hub(None, test=True)
#     s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1)
#     s.dt_model.set_hour(0)
#     s.dt_model.set_date(date(2023,7,30))
#     await hub.async_setup([s])
#     np1 = MockNordpool(today=_p.P230731, tomorrow=[], average=mean(_p.P230731), currency="EUR", price_in_cent=False, tomorrow_valid=False)
#     await hub.spotprice.async_set_dto(np1)    
#     assert len(s.all_sequences) == 23
#     s.dt_model.set_hour(13)
#     np2 = MockNordpool(today=_p.P230731, tomorrow=_p.P230801, average=mean(_p.P230731), currency="EUR", price_in_cent=False, tomorrow_valid=True)
#     await hub.spotprice.async_set_dto(np2)
#     tt = await hub.async_get_sensor_updates(s)
#     #s.dt_model.set_hour(19)
#     # tt2 = await hub.async_get_sensor_updates(s)
#     # print(f"best: {tt2.get('best_close_start')}")
#     ttt = sorted(tt.get("all_sequences"), key=lambda x: x.dt_start)
#     for t in ttt:
#         print(_make_hours_display(t))
#         #print(t.dt_start)
#     assert 1 > 2

@pytest.mark.asyncio
async def test_custom_consumption_valid():    
    s = NextSensor(consumption_type=ConsumptionType.Custom, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10, custom_consumption_pattern="0.5,0.5") 
    s.dt_model.set_hour(4)   
    await s.async_update_sensor((_p.P230729BE,[]))   
    assert s.custom_consumption_pattern_list == [0.5,0.5]

@pytest.mark.asyncio
async def test_custom_consumption_invalid():    
    with pytest.raises(Exception):   
        s = NextSensor(consumption_type=ConsumptionType.Custom, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10, custom_consumption_pattern="0.f5,0.5") 


def _check_hourmodel(model: PeriodModel) -> bool:
    if model is None:
        return False
    elif not model.is_valid:
        print("not valid")
        return False
    return True

def _get_tomorrow_assignation(comparer: bool) -> str:
    return "⁺¹" if comparer else ""

def _add_now_to_date(model: PeriodModel) -> str:
    return ">> " if model.dt_start.day == datetime.now().day and model.dt_start.hour == datetime.now().hour else ""

def _make_hours_display(model: PeriodModel) -> str:
    if not _check_hourmodel(model):
        return ""
    tomorrow1: str = _get_tomorrow_assignation(model.dt_start.day > datetime.now().day)
    tomorrow2: str = _get_tomorrow_assignation(model.dt_end.day > datetime.now().day)
    ret = f"{model.dt_start.strftime('%H:%M')}{tomorrow1}-{model.dt_end.strftime('%H:%M')}{tomorrow2}"
    return f"{_add_now_to_date(model)}{ret}"

@pytest.mark.asyncio
async def test_correct_sorting_negative_prices_2():    
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=120, total_consumption_in_kwh=10) 
    s.dt_model.set_hour(2)   
    await s.async_update_sensor((_p.PNEGATIVE2,[]), use_cent=False)        
    for h in s.all_sequences:
        print(h)
    all_seq_copy = s.all_sequences[:]
    all_seq_copy.sort(key=lambda x: (x.comparer, x.dt_start))
    assert all_seq_copy == s.all_sequences
    #assert 1 > 2


@pytest.mark.asyncio
async def test_cheapest_hour_update_hourly():
    s = NextSensor(consumption_type=ConsumptionType.PeakIn, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=62, total_consumption_in_kwh=1.1, update_by=UpdateBy.HOUR)
    s.dt_model.set_date(date(2023,7,30))
    s.dt_model.set_hour(20)
    await s.async_update_sensor([_p.P230731,_p.P230801])
    print(s.best_close_start)
    print("---------")
    for s in s.all_sequences:
        print(s)
    
    assert 1 > 2

@pytest.mark.asyncio
async def test_price_change_per_minute():
    s = NextSensor(consumption_type=ConsumptionType.Flat, name="test", hass_entity_id="sensor.test", total_duration_in_minutes=60, total_consumption_in_kwh=1, update_by=UpdateBy.MINUTE)
    s.dt_model.set_date(date(2023,7,30))
    s.dt_model.set_hour(0)
    s.dt_model.set_minute(0)
    await s.async_update_sensor([[0.1, 1],[]])
    for seq in s.all_sequences:
        print(seq.dt_start, seq.price)
    s.dt_model.set_minute(45)
    await s.async_update_sensor([[0.1, 1],[]])
    print('---')
    for seq in s.all_sequences:
        print(seq.dt_start, seq.price)
    assert 1 > 2
