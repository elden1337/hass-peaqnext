# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run tests:**
```bash
pytest custom_components/peaqnext/test/
```

**Run a single test file:**
```bash
pytest custom_components/peaqnext/test/test_nextsensor.py
```

**Lint (syntax errors and undefined names only — CI fails on these):**
```bash
flake8 custom_components --count --select=E9,F63,F7,F82 --show-source --statistics
```

**Lint (all warnings, non-blocking):**
```bash
flake8 custom_components --count --exit-zero --statistics
```

## Architecture

This is a Home Assistant custom integration (`domain: peaqnext`) that suggests the cheapest time window to run appliances (washing machines, dryers, etc.) based on electricity spot prices.

**Entry point:** `custom_components/peaqnext/__init__.py`
- `async_setup_entry` instantiates a `Hub`, builds `NextSensor` objects from config, and forwards setup to the `sensor` platform.

**Hub** (`service/hub.py`)
- Central coordinator. Holds all `NextSensor` instances and the active `ISpotPrice` source.
- Subscribes to state-change events on the spot price entity via `async_track_state_change_event`.
- `async_get_updates(sensor_id)` is the main call path from HA sensors — forces a price refresh if >60s stale.

**Spot price sources** (`service/spotprice/`)
- `SpotPriceFactory.create()` auto-detects whether EnergiDataService or Nordpool is available in HA and returns the appropriate `ISpotPrice` implementation.
- Both implementations expose `.prices` (today) and `.prices_tomorrow` as plain `list[float]`.

**Sensor model** (`service/models/sensor_model.py` → `NextSensor`)
- Holds per-appliance config: `ConsumptionType`, duration, kWh, non-hours, `UpdateBy` (minute vs. hour), `CalculateBy` (start vs. end time).
- `async_update_sensor(prices_tuple)` recomputes `best_start` and `best_close_start` (cheapest within the configured look-ahead window).

**Consumption pattern / segments** (`service/segments.py`, `service/models/consumption_type.py`)
- `ConsumptionType` enum defines the shape of power draw over the cycle (Flat, PeakBeginning, PeakEnd, PeakMiddle, PeakBeginningAndEnd, Custom).
- The segments logic translates a pattern + total kWh into per-slot costs for each candidate start time.

**Config flow** (`config_flow.py`)
- Supports multiple sensors per config entry; each sensor's config dict is stored under `CONF_SENSORS` as a list.

**Tests** (`test/`)
- Use `pytest-asyncio`. Tests instantiate `NextSensor` directly with `test=True` (bypasses HA state machine).
- Price fixtures live in `test/prices.py`.
