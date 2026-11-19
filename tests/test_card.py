"""Tests of the card side: websocket command and the registration of the card."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.mannito.const import DOMAIN
from custom_components.mannito.frontend import CARD_FILE, CARD_URL, async_register_card

from .conftest import API, AREA_ID, BOARD_ID, setup_integration

FAN = "11111111-0000-4000-8000-000000000001"


async def test_area_for_the_card(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
) -> None:
    """The card gets the entities of the grow area by key and the outputs, assigned ones first."""
    board["areas"][0]["devices"] = [{"deviceId": FAN, "function": "Exhaust", "functionName": "Abluft"}]
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    devices = dr.async_get(hass)
    area = devices.async_get_child_device_by_identifier((DOMAIN, f"area_{AREA_ID}"), mock_config_entry.entry_id)
    assert area is not None

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "mannito/area", "device_id": area.id})
    result = (await client.receive_json())["result"]

    assert result["name"] == "Green Poison"
    assert result["can_control"] is True
    assert result["entities"]["temperature"] == "sensor.zelt_green_poison_temperature"
    assert result["entities"]["p2_dryback"] == "number.zelt_green_poison_p2_trigger_below_peak"
    assert result["board_entities"]["firmware"] == "update.zelt_firmware"
    fan = result["outputs"][0]
    assert fan["device_id"] == FAN
    assert fan["assigned"] is True
    assert fan["function_name"] == "Abluft"
    assert fan["entities"] == {
        "control": "fan.zelt_abluft",
        "automatic": "button.zelt_abluft_automatic",
        "manual_override": "binary_sensor.zelt_abluft_manual_operation",
    }
    assert [o["assigned"] for o in result["outputs"]] == [True, False, False, False]

    board_device = devices.async_get_device_by_identifier((DOMAIN, BOARD_ID), mock_config_entry.entry_id)
    assert board_device is not None
    await client.send_json_auto_id({"type": "mannito/area", "device_id": board_device.id})
    answer = await client.receive_json()
    assert answer["success"] is False
    assert answer["error"]["code"] == "not_an_area"


async def test_card_is_served_and_loaded(hass: HomeAssistant) -> None:
    """With a web server and a frontend the card is served with a version and added to every dashboard."""
    hass.config.components.add("frontend")
    http = MagicMock()
    http.async_register_static_paths = AsyncMock()
    hass.http = http
    with patch("homeassistant.components.frontend.add_extra_js_url") as add_url:
        await async_register_card(hass)

    paths = http.async_register_static_paths.call_args.args[0]
    assert paths[0].url_path == CARD_URL
    assert paths[0].path == str(CARD_FILE)
    assert CARD_FILE.is_file()
    assert add_url.call_args.args[1].startswith(f"{CARD_URL}?v=")


async def test_no_card_without_frontend(hass: HomeAssistant) -> None:
    """Without a web server nothing is registered."""
    hass.http = None
    await async_register_card(hass)
