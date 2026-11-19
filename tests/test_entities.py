"""Tests of the entities and actions."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.fan import ATTR_PERCENTAGE, SERVICE_SET_PERCENTAGE
from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.components.number import ATTR_VALUE, SERVICE_SET_VALUE
from homeassistant.components.select import ATTR_OPTION, SERVICE_SELECT_OPTION
from homeassistant.components.update import SERVICE_INSTALL
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_OPEN_VALVE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.mannito.const import DOMAIN
from custom_components.mannito.diagnostics import async_get_config_entry_diagnostics

from .conftest import API, AREA_ID, calls_to, setup_integration

FAN = "11111111-0000-4000-8000-000000000001"
LAMP = "11111111-0000-4000-8000-000000000002"
VALVE = "11111111-0000-4000-8000-000000000003"


@pytest.fixture
async def loaded(
    hass: HomeAssistant, mock_cloud: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> AiohttpClientMocker:
    """The board set up against the mocked cloud."""
    await setup_integration(hass, mock_config_entry)
    return mock_cloud


async def test_states(hass: HomeAssistant, loaded: AiohttpClientMocker) -> None:
    """The values of the cloud show up as states."""
    expected = {
        "sensor.zelt_green_poison_temperature": "24.6",
        "sensor.zelt_green_poison_vpd": "1.21",
        "sensor.zelt_green_poison_target_vpd": "1.15",
        "sensor.zelt_green_poison_status": "ok",
        "sensor.zelt_green_poison_grow_phase": "Blüte Woche 1–3",
        "sensor.zelt_green_poison_substrate_moisture": "41.9",
        "sensor.zelt_green_poison_shots_today": "3",
        "sensor.zelt_green_poison_tank_volume": "8.2",
        "binary_sensor.zelt_green_poison_day": "on",
        "binary_sensor.zelt_green_poison_emergency_mode": "off",
        "binary_sensor.zelt_connectivity": "on",
        "fan.zelt_abluft": "on",
        "light.zelt_lampe": "on",
        "valve.zelt_ventil_rechts": "closed",
        "switch.zelt_befeuchter": "off",
        "binary_sensor.zelt_befeuchter_manual_operation": "on",
        "select.zelt_green_poison_climate_control": "pi",
        "select.zelt_green_poison_irrigation": "dryback",
        "select.zelt_green_poison_dryback_strategy": "custom",
        "number.zelt_green_poison_p2_trigger_below_peak": "8.9",
        "number.zelt_green_poison_water_per_pot_and_day_at_most": "1500",
        "switch.zelt_green_poison_control": "on",
        "update.zelt_firmware": "on",
        "sensor.mannito_vpd_modul_temperatur_zelt": "24.6",
        "sensor.zelt_substrat_topf_3": "41.9",
    }
    actual = {entity_id: getattr(hass.states.get(entity_id), "state", None) for entity_id in expected}
    assert actual == expected
    assert hass.states.get("fan.zelt_abluft").attributes[ATTR_PERCENTAGE] == 45
    assert hass.states.get("sensor.zelt_green_poison_co2") is None, "no CO2 in this area"


async def test_switching_outputs(hass: HomeAssistant, loaded: AiohttpClientMocker) -> None:
    """Fans, lamps and valves send their commands; a valve opens only for a short time."""
    await hass.services.async_call(
        "fan", SERVICE_SET_PERCENTAGE, {ATTR_ENTITY_ID: "fan.zelt_abluft", ATTR_PERCENTAGE: 70}, blocking=True
    )
    await hass.services.async_call(
        "light", SERVICE_TURN_ON, {ATTR_ENTITY_ID: "light.zelt_lampe", ATTR_BRIGHTNESS: 128}, blocking=True
    )
    await hass.services.async_call(
        "valve", SERVICE_OPEN_VALVE, {ATTR_ENTITY_ID: "valve.zelt_ventil_rechts"}, blocking=True
    )
    await hass.services.async_call(
        DOMAIN, "open_valve", {ATTR_ENTITY_ID: "valve.zelt_ventil_rechts", "duration": 30}, blocking=True
    )
    await hass.services.async_call(
        "switch", SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "switch.zelt_befeuchter"}, blocking=True
    )
    await hass.services.async_call(
        "button", SERVICE_PRESS, {ATTR_ENTITY_ID: "button.zelt_abluft_automatic"}, blocking=True
    )

    assert calls_to(loaded, "POST", f"/devices/{FAN}/state") == [{"on": True, "powerPercent": 70}]
    assert calls_to(loaded, "POST", f"/devices/{LAMP}/state") == [{"on": True, "powerPercent": 50}]
    assert calls_to(loaded, "POST", f"/devices/{VALVE}/state") == [
        {"on": True, "durationSeconds": 10},
        {"on": True, "durationSeconds": 30},
    ]
    assert calls_to(loaded, "POST", f"/devices/{FAN}/automatic") == [{}]


async def test_open_valve_refuses_long_openings(hass: HomeAssistant, loaded: AiohttpClientMocker) -> None:
    """The action takes at most 60 seconds."""
    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN, "open_valve", {ATTR_ENTITY_ID: "valve.zelt_ventil_rechts", "duration": 61}, blocking=True
        )
    assert calls_to(loaded, "POST", f"/devices/{VALVE}/state") == []


async def test_configuring_the_area(hass: HomeAssistant, loaded: AiohttpClientMocker) -> None:
    """Selects, numbers and the control switch change the grow area."""
    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.zelt_green_poison_climate_control", ATTR_OPTION: "fuzzy"},
        blocking=True,
    )
    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.zelt_green_poison_dryback_strategy", ATTR_OPTION: "generative"},
        blocking=True,
    )
    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.zelt_green_poison_p2_trigger_below_peak", ATTR_VALUE: 9.5},
        blocking=True,
    )
    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.zelt_green_poison_p1_shot_per_pot", ATTR_VALUE: 240},
        blocking=True,
    )
    await hass.services.async_call(
        "switch", SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "switch.zelt_green_poison_control"}, blocking=True
    )
    await hass.services.async_call("update", SERVICE_INSTALL, {ATTR_ENTITY_ID: "update.zelt_firmware"}, blocking=True)

    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/climate-control") == [{"mode": "FUZZY"}]
    assert calls_to(loaded, "PATCH", f"/areas/{AREA_ID}/irrigation") == [
        {"strategy": "Generative"},
        {"p2DrybackPct": 9.5},
        {"p1ShotMl": 240},
    ]
    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/enabled") == [{"enabled": False}]
    assert calls_to(loaded, "POST", "/firmware/update") == [{"force": False}]


async def test_area_actions(
    hass: HomeAssistant, loaded: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """The actions reach the grow area chosen as device."""
    devices = dr.async_get(hass)
    area = devices.async_get_child_device_by_identifier((DOMAIN, f"area_{AREA_ID}"), mock_config_entry.entry_id)
    assert area is not None
    await hass.services.async_call(DOMAIN, "run_valves", {"area": area.id, "seconds": 8}, blocking=True)
    await hass.services.async_call(
        DOMAIN,
        "grow_cycle_action",
        {"area": area.id, "action": "set_lights_on", "lights_on": "08:30:00"},
        blocking=True,
    )
    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/irrigation/run") == [{"seconds": 8, "mlPerPot": None}]
    assert calls_to(loaded, "POST", f"/areas/{AREA_ID}/grow-cycle") == [
        {"action": "SetLightsOn", "days": None, "lightsOn": "08:30", "useCo2": None}
    ]

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "grow_cycle_action", {"area": area.id, "action": "postpone"}, blocking=True
        )
    board = devices.async_get_device_by_identifier(
        (DOMAIN, "c0ddf638-1007-4162-a038-e7753a4b75c1"), mock_config_entry.entry_id
    )
    assert board is not None
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "run_valves", {"area": board.id, "seconds": 8}, blocking=True)


async def test_refused_command_shows_the_reason(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """A refusal of the cloud reaches the user with its German reason; a missing right is named as such."""
    aioclient_mock.get(API, json=board)
    aioclient_mock.post(
        f"{API}/devices/{FAN}/state",
        status=409,
        json={"status": 409, "title": "Refused", "detail": "Controller offline."},
        headers={"Content-Type": "application/problem+json"},
    )
    aioclient_mock.post(f"{API}/devices/{LAMP}/state", status=403)
    await setup_integration(hass, mock_config_entry)

    with pytest.raises(HomeAssistantError) as refused:
        await hass.services.async_call("fan", SERVICE_TURN_ON, {ATTR_ENTITY_ID: "fan.zelt_abluft"}, blocking=True)
    assert refused.value.translation_key == "command_failed"
    assert refused.value.translation_placeholders == {"error": "Controller offline."}

    with pytest.raises(HomeAssistantError) as forbidden:
        await hass.services.async_call("light", SERVICE_TURN_ON, {ATTR_ENTITY_ID: "light.zelt_lampe"}, blocking=True)
    assert forbidden.value.translation_key == "missing_right"


async def test_diagnostics_hide_the_token(
    hass: HomeAssistant, loaded: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """The diagnostics never contain the token."""
    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert "mnt_" not in str(diagnostics)
    assert diagnostics["board"]["board"]["name"] == "Zelt"
