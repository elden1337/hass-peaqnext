import pytest

from custom_components.peaqnext.service.spotprice.spotprice_dto import (
    EnergiDataServiceDTO,
    NordpoolDTO,
)
from custom_components.peaqnext.test.conftest import fake_state


async def test_nordpool_parses_all_fields():
    ret = fake_state(
        state="0.42",
        today=[1.0, 2.0],
        tomorrow=[3.0],
        tomorrow_valid=True,
        currency="SEK",
        average=1.5,
        price_in_cent=True,
    )
    dto = NordpoolDTO()
    await dto.set_model(ret)
    assert dto.today == [1.0, 2.0]
    assert dto.tomorrow == [3.0]
    assert dto.tomorrow_valid is True
    assert dto.currency == "SEK"
    assert dto.state == "0.42"
    assert dto.average == 1.5
    assert dto.price_in_cent is True


async def test_nordpool_defaults_when_optional_attributes_missing():
    dto = NordpoolDTO()
    await dto.set_model(fake_state(today=[1.0]))
    assert dto.price_in_cent is False
    assert dto.average == 0.0
    assert dto.tomorrow_valid is False


async def test_nordpool_tomorrow_none_becomes_empty_list():
    dto = NordpoolDTO()
    ret = fake_state(today=[1.0])
    ret.attributes["tomorrow"] = None
    await dto.set_model(ret)
    assert dto.tomorrow == []


async def test_nordpool_unparsable_average_falls_back_to_zero():
    dto = NordpoolDTO()
    await dto.set_model(fake_state(today=[1.0], average="not-a-number"))
    assert dto.average == 0


async def test_missing_today_leaves_dto_untouched():
    """A state without 'today' must not raise and must not half-populate."""
    ret = fake_state()
    del ret.attributes["today"]
    dto = NordpoolDTO()
    await dto.set_model(ret)
    assert dto.today == []
    assert dto.currency == ""


async def test_energidataservice_average_is_computed_from_today():
    dto = EnergiDataServiceDTO()
    await dto.set_model(fake_state(today=[1.0, 2.0, 3.0]))
    assert dto.average == 2.0


async def test_energidataservice_use_cent_flag():
    dto = EnergiDataServiceDTO()
    await dto.set_model(fake_state(today=[1.0], use_cent=True))
    assert dto.price_in_cent is True


async def test_energidataservice_empty_today_average_is_zero():
    dto = EnergiDataServiceDTO()
    await dto.set_model(fake_state(today=[]))
    assert dto.average == 0
