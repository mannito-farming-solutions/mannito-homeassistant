"""Tests of phase targets, lights-on time, calendar, plants, records, tank book and switching feedback."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.number import ATTR_VALUE, SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.mannito.const import DOMAIN

from .conftest import API, AREA_ID, PLANT_ID, PLANTING_ID, calls_to, setup_integration

SOCKET = "11111111-0000-4000-8000-000000000004"


@pytest.fixture
async def loaded(
    hass: HomeAssistant, mock_cloud: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> AiohttpClientMocker:
    """The board set up against the mocked cloud."""
    await setup_integration(hass, mock_config_entry)
    return mock_cloud


async def test_phase_targets_and_lights_on(hass: HomeAssistant, loaded: AiohttpClientMocker) -> None:
    """The targets of the phase are numbers, lights-on is a time; both change the grow cycle."""
    assert hass.states.get("number.zelt_green_poison_day_temperature").state == "25.0"
    assert hass.states.get("time.zelt_green_poison_lights_on").state == "09:00:00"

    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.zelt_green_poison_night_vpd", ATTR_VALUE: 0.9},
        blocking=True,
    )
    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.zelt_green_poison_circulation", ATTR_VALUE: 55},
        blocking=True,
    )
    await hass.services.async_call(
        "time", "set_value", {ATTR_ENTITY_ID: "time.zelt_green_poison_lights_on", "time": "08:30:00"}, blocking=True
    )

    assert calls_to(loaded, "PATCH", f"/areas/{AREA_ID}/phase-values") == [{"nightVpdKpa": 0.9}, {"circulationPct": 55}]
    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/grow-cycle") == [
        {"action": "SetLightsOn", "days": None, "lightsOn": "08:30", "useCo2": None}
    ]


async def test_calendar_of_the_phases(hass: HomeAssistant, loaded: AiohttpClientMocker) -> None:
    """The calendar shows the current phase and lists done and planned ones."""
    state = hass.states.get("calendar.zelt_green_poison_grow_phases")
    assert state.state == "on"
    assert state.attributes["message"] == "Blüte Woche 1–3"

    events = await hass.services.async_call(
        "calendar",
        "get_events",
        {
            ATTR_ENTITY_ID: "calendar.zelt_green_poison_grow_phases",
            "start_date_time": "2026-10-01T00:00:00+00:00",
            "duration": {"days": 120},
        },
        blocking=True,
        return_response=True,
    )
    assert [e["summary"] for e in events["calendar.zelt_green_poison_grow_phases"]["events"]] == [
        "Wachstum",
        "Blüte Woche 1–3",
        "Blüte Woche 4–6",
    ]


async def test_plants_and_their_records(
    hass: HomeAssistant, loaded: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """Every plant is a device with its height; measurements and notes reach its planting."""
    assert hass.states.get("sensor.zelt_green_poison_3_height").state == "37.0"
    assert hass.states.get("sensor.zelt_green_poison_open_problems").state == "1"

    devices = dr.async_get(hass)
    plant = devices.async_get_child_device_by_identifier((DOMAIN, f"plant_{PLANT_ID}"), mock_config_entry.entry_id)
    area = devices.async_get_child_device_by_identifier((DOMAIN, f"area_{AREA_ID}"), mock_config_entry.entry_id)
    assert plant is not None and plant.name == "Green Poison #3"
    assert area is not None

    await hass.services.async_call(
        DOMAIN, "record_measurement", {"target": plant.id, "measurement": "height", "value": 38.5}, blocking=True
    )
    await hass.services.async_call(
        DOMAIN,
        "record_note",
        {"target": area.id, "condition": "warning", "note": "Gelbe Spitzen", "problem": True},
        blocking=True,
    )

    assert calls_to(loaded, "POST", f"/plantings/{PLANTING_ID}/measurements") == [
        {"target": "PlantHeight", "value": 385.0, "plantId": PLANT_ID, "note": None}
    ]
    assert calls_to(loaded, "POST", f"/plantings/{PLANTING_ID}/inspections") == [
        {"result": "Warning", "note": "Gelbe Spitzen", "plantId": None, "problem": True}
    ]


async def test_record_needs_a_plant_when_an_area_has_several_plantings(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """A grow area with two plantings does not know which one is meant."""
    second = {**board["areas"][0]["plantings"][0], "id": "44444444-0000-4000-8000-000000000002", "plants": []}
    board["areas"][0]["plantings"].append(second)
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    area = dr.async_get(hass).async_get_child_device_by_identifier(
        (DOMAIN, f"area_{AREA_ID}"), mock_config_entry.entry_id
    )

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, "record_measurement", {"target": area.id, "measurement": "height", "value": 30}, blocking=True
        )
    assert err.value.translation_key == "choose_plant"


async def test_tank_book_and_field_capacity(
    hass: HomeAssistant, loaded: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """Tank entries, tank readings and the field capacity reach the grow area."""
    area = dr.async_get(hass).async_get_child_device_by_identifier(
        (DOMAIN, f"area_{AREA_ID}"), mock_config_entry.entry_id
    )
    await hass.services.async_call(
        DOMAIN, "tank_entry", {"area": area.id, "kind": "top_up", "liters": 2.5}, blocking=True
    )
    await hass.services.async_call(DOMAIN, "tank_reading", {"area": area.id, "ec": 1.6, "ph": 5.9}, blocking=True)
    await hass.services.async_call(
        "button",
        "press",
        {ATTR_ENTITY_ID: "button.zelt_green_poison_field_capacity_from_current_reading"},
        blocking=True,
    )

    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/tank/entries") == [
        {"kind": "TopUp", "liters": 2.5, "note": None}
    ]
    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/tank/readings") == [
        {"ecMs": 1.6, "ph": 5.9, "temperatureC": None}
    ]
    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/field-capacity") == [{"vwcPct": None}]


async def test_a_switched_output_shows_its_new_state_until_the_board_reports(
    hass: HomeAssistant, loaded: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    """The cloud still reports the old state right after the command: the switch keeps the new one and asks again later."""
    await hass.services.async_call("switch", SERVICE_TURN_ON, {ATTR_ENTITY_ID: "switch.zelt_befeuchter"}, blocking=True)
    assert hass.states.get("switch.zelt_befeuchter").state == "on"
    polls = len(calls_to(loaded, "GET", ""))

    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(calls_to(loaded, "GET", "")) > polls, "asks the cloud again a few seconds later"
    assert hass.states.get("switch.zelt_befeuchter").state == "on", "the board has not reported yet"


async def test_rate_limit_waits(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """A 429 of the cloud makes the setup retry later instead of failing."""
    aioclient_mock.get(API, status=429, headers={"Retry-After": "30"})
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state.name == "SETUP_RETRY"


async def test_stale_board_sensor_shows_unknown(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """A sensor value older than 15 minutes is not shown."""
    board["sensors"][0]["valueAtUtc"] = "2026-01-01T00:00:00Z"
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get("sensor.mannito_vpd_modul_temperatur_zelt").state == "unknown"
