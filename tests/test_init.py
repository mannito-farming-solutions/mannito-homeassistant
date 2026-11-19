"""Tests of setup, unload, failures, and devices that come and go."""

from __future__ import annotations

from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.mannito.const import DOMAIN, SCAN_INTERVAL

from .conftest import API, AREA_ID, BOARD_ID, setup_integration


async def test_setup_and_unload(
    hass: HomeAssistant, mock_cloud: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """The board sets up with its devices and unloads again."""
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    devices = dr.async_get(hass)
    entry_id = mock_config_entry.entry_id
    board = devices.async_get_device_by_identifier((DOMAIN, BOARD_ID), entry_id)
    area = devices.async_get_child_device_by_identifier((DOMAIN, f"area_{AREA_ID}"), entry_id)
    bus = devices.async_get_device_by_identifier((DOMAIN, f"{BOARD_ID}_bus_5C013B543614"), entry_id)
    assert board is not None and board.sw_version == "2.14.2"
    assert area is not None and area.parent_device_id == board.id and area.name == "Green Poison"
    assert bus is not None and bus.via_device_id == board.id and bus.serial_number == "5C013B543614"

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_revoked_token_starts_reauth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """A token the cloud no longer accepts asks for a new one."""
    aioclient_mock.get(API, status=401)
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


async def test_unreachable_cloud_retries(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """An unreachable cloud lets Home Assistant try again later."""
    aioclient_mock.get(API, status=502)
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_entities_unavailable_while_cloud_down(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """The entities turn unavailable when the cloud stops answering and come back."""
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get("sensor.zelt_green_poison_temperature").state == "24.6"

    aioclient_mock.clear_requests()
    aioclient_mock.get(API, status=503)
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.zelt_green_poison_temperature").state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json=board)
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.zelt_green_poison_temperature").state == "24.6"


async def test_new_and_removed_areas(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A grow area added later gets its entities; a removed one loses its device."""
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)

    second = {**board["areas"][0], "id": "ee000000-0000-4000-8000-000000000002", "name": "Schrank"}
    changed = {**board, "areas": [second]}
    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json=changed)
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    devices = dr.async_get(hass)
    entry_id = mock_config_entry.entry_id
    assert devices.async_get_child_device_by_identifier((DOMAIN, f"area_{AREA_ID}"), entry_id) is None
    assert devices.async_get_child_device_by_identifier((DOMAIN, "area_ee000000-0000-4000-8000-000000000002"), entry_id)
    assert hass.states.get("sensor.zelt_schrank_temperature").state == "24.6"


async def test_read_only_token(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
) -> None:
    """A token that may only read gets no switching or configuring entities."""
    board["access"]["canControl"] = False
    board["access"]["canConfigure"] = False
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)

    entities = er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    domains = {entity.domain for entity in entities}
    assert not domains & {"fan", "light", "switch", "valve", "button", "select", "number"}
    assert hass.states.get("binary_sensor.zelt_abluft").state == "on"
    assert hass.states.get("update.zelt_firmware").attributes["supported_features"] == 0
