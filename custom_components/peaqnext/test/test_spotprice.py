"""ISpotPrice base logic, the two updaters and the factory."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.peaqnext.service.spotprice.const import (
    ENERGIDATASERVICE,
    ENERGIDATASERVICE_SENSOR,
    NORDPOOL,
)
from custom_components.peaqnext.service.spotprice.energidataservice import (
    EnergiDataServiceUpdater,
)
from custom_components.peaqnext.service.spotprice.nordpool import NordPoolUpdater
from custom_components.peaqnext.service.spotprice.spotprice_dto import NordpoolDTO
from custom_components.peaqnext.service.spotprice.spotprice_factory import (
    SpotPriceFactory,
)
from custom_components.peaqnext.test.conftest import fake_state

NP_MODULE = "custom_components.peaqnext.service.spotprice.nordpool"
EDS_MODULE = "custom_components.peaqnext.service.spotprice.energidataservice"


def _updater(cls, hub):
    u = cls(hub, test=True)
    u.state_machine = hub.state_machine
    return u


# --- ISpotPrice.async_update_set_prices ---------------------------------


async def _dto(**kw):
    dto = NordpoolDTO()
    await dto.set_model(fake_state(**kw))
    return dto


async def test_set_prices_reports_change_then_no_change(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    dto = await _dto(today=[1.0, 2.0], tomorrow_valid=False)
    assert await u.async_update_set_prices(dto) is True
    assert u.prices == [1.0, 2.0]
    # Same today and still no tomorrow: tomorrow reset is always reported as change
    # (documents current behaviour: tomorrow-invalid path always returns True).
    assert await u.async_update_set_prices(dto) is True


async def test_set_prices_stable_when_tomorrow_valid_and_unchanged(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    dto = await _dto(today=[1.0], tomorrow=[2.0], tomorrow_valid=True)
    assert await u.async_update_set_prices(dto) is True
    assert await u.async_update_set_prices(dto) is False
    assert u.prices_tomorrow == [2.0]


async def test_set_prices_clears_tomorrow_when_invalid(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    await u.async_update_set_prices(
        await _dto(today=[1.0], tomorrow=[2.0], tomorrow_valid=True)
    )
    await u.async_update_set_prices(
        await _dto(today=[1.0], tomorrow=[2.0], tomorrow_valid=False)
    )
    assert u.prices_tomorrow == []


async def test_set_prices_stores_currency_and_cent_flag(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    await u.async_update_set_prices(
        await _dto(today=[1.0], currency="EUR", price_in_cent=True)
    )
    assert u.currency == "EUR"
    assert u.use_cent is True


# --- async_set_dto / async_update_spotprice -----------------------------


async def test_nordpool_set_dto_pushes_prices_to_hub(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    await u.async_set_dto(fake_state(today=[1.0, 2.0]))
    fake_hub.async_update_prices.assert_awaited_once_with(([1.0, 2.0], []))
    assert u.is_initialized is True


async def test_set_dto_does_not_push_when_nothing_changed(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    state = fake_state(today=[1.0], tomorrow=[2.0], tomorrow_valid=True)
    await u.async_set_dto(state)
    await u.async_set_dto(state)
    assert fake_hub.async_update_prices.await_count == 1


async def test_energidataservice_set_dto_pushes_prices_to_hub(fake_hub):
    u = _updater(EnergiDataServiceUpdater, fake_hub)
    await u.async_set_dto(fake_state(today=[3.0]))
    fake_hub.async_update_prices.assert_awaited_once_with(([3.0], []))


async def test_update_spotprice_reads_entity_state(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    u._entity = "sensor.nordpool_kwh_se3_sek"
    fake_hub.state_machine.states.get.return_value = fake_state(today=[9.0])
    await u.async_update_spotprice()
    fake_hub.state_machine.states.get.assert_called_with("sensor.nordpool_kwh_se3_sek")
    assert u.prices == [9.0]


async def test_update_spotprice_handles_missing_state(fake_hub):
    u = _updater(NordPoolUpdater, fake_hub)
    u._entity = "sensor.gone"
    fake_hub.state_machine.states.get.return_value = None
    await u.async_update_spotprice()  # must not raise
    fake_hub.async_update_prices.assert_not_awaited()


# --- NordPoolUpdater.setup ----------------------------------------------


def _nordpool_with_sources(fake_hub, sources, states=None):
    """Run NordPoolUpdater.setup() against fake entity_sources / states."""
    fake_hub.state_machine.states.get.side_effect = lambda e: (states or {}).get(e)
    u = _updater(NordPoolUpdater, fake_hub)
    with patch(f"{NP_MODULE}.entity_sources", return_value=sources), patch(
        f"{NP_MODULE}.asyncio.run_coroutine_threadsafe"
    ) as run:
        u.setup()
    return u, run


def _src(*entity_ids, domain=NORDPOOL):
    return {e: {"domain": domain} for e in entity_ids}


def test_nordpool_single_entity_is_selected(fake_hub):
    u, run = _nordpool_with_sources(fake_hub, _src("sensor.np"))
    assert u.entity == "sensor.np"
    run.assert_called_once()
    run.call_args.args[0].close()  # avoid "never awaited" warning


def test_nordpool_ignores_other_integrations(fake_hub):
    u, run = _nordpool_with_sources(
        fake_hub,
        {**_src("sensor.np"), **_src("sensor.other", domain="tibber")},
    )
    assert u.entity == "sensor.np"
    run.call_args.args[0].close()


def test_nordpool_no_entities_leaves_entity_unset(fake_hub):
    u, run = _nordpool_with_sources(fake_hub, {})
    assert not u.entity
    run.assert_not_called()


def test_nordpool_multiple_picks_sensor_with_additional_costs(fake_hub):
    states = {
        "sensor.a": fake_state(additional_costs_current_hour=0),
        "sensor.b": fake_state(additional_costs_current_hour=0.25),
    }
    u, run = _nordpool_with_sources(fake_hub, _src("sensor.a", "sensor.b"), states)
    assert u.entity == "sensor.b"
    run.call_args.args[0].close()


def test_nordpool_multiple_without_distinguishing_attribute_is_unresolved(fake_hub):
    states = {
        "sensor.a": fake_state(additional_costs_current_hour=0),
        "sensor.b": fake_state(),
    }
    u, run = _nordpool_with_sources(fake_hub, _src("sensor.a", "sensor.b"), states)
    assert not u.entity
    run.assert_not_called()


# --- EnergiDataServiceUpdater.setup -------------------------------------


def test_energidataservice_setup_sets_fixed_entity(fake_hub):
    fake_hub.state_machine.states.get.return_value = fake_state(state="0.4")
    u = _updater(EnergiDataServiceUpdater, fake_hub)
    with patch(f"{EDS_MODULE}.asyncio.run_coroutine_threadsafe") as run:
        u.setup()
    assert u.entity == ENERGIDATASERVICE_SENSOR
    run.assert_called_once()
    run.call_args.args[0].close()


def test_energidataservice_setup_missing_sensor_does_not_raise(fake_hub):
    fake_hub.state_machine.states.get.return_value = None
    u = _updater(EnergiDataServiceUpdater, fake_hub)
    u.setup()
    assert not u.entity


# --- Factory -------------------------------------------------------------


def test_factory_prefers_energidataservice_when_sensor_exists():
    hass = MagicMock()
    hass.states.get.return_value = object()
    assert SpotPriceFactory.test_connections(hass) == ENERGIDATASERVICE
    hass.states.get.assert_called_with(ENERGIDATASERVICE_SENSOR)


def test_factory_falls_back_to_nordpool():
    hass = MagicMock()
    hass.states.get.return_value = None
    assert SpotPriceFactory.test_connections(hass) == NORDPOOL


def test_factory_create_in_test_mode_returns_nordpool(fake_hub):
    assert isinstance(SpotPriceFactory.create(fake_hub, test=True), NordPoolUpdater)


def test_factory_create_selects_implementation(fake_hub):
    fake_hub.state_machine.states.get.return_value = None
    with patch.object(NordPoolUpdater, "setup"), patch.object(
        EnergiDataServiceUpdater, "setup"
    ):
        assert isinstance(SpotPriceFactory.create(fake_hub), NordPoolUpdater)
        fake_hub.state_machine.states.get.return_value = object()
        assert isinstance(
            SpotPriceFactory.create(fake_hub), EnergiDataServiceUpdater
        )
