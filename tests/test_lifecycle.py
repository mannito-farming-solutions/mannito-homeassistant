"""Tests of a clean removal, a new token and things the board no longer has."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import CONF_API_TOKEN, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.mannito.const import DOMAIN, SCAN_INTERVAL
from custom_components.mannito.frontend import CARD, async_register_card

from .conftest import API, AREA_ID, PLANT_ID, TOKEN, URL, setup_integration

NEW_TOKEN = "mnt_" + "B" * 43
FAN = "11111111-0000-4000-8000-000000000001"


def _revokes(mock: AiohttpClientMocker, url: str, token: str) -> list[Any]:
    """The DELETE requests that revoked this token."""
    return [
        call
        for call in mock.mock_calls
        if call[0].upper() == "DELETE" and str(call[1]) == f"{url}/api/v1/board/token" and token in str(call[3])
    ]


def _entities(hass: HomeAssistant, entry: MockConfigEntry) -> list[er.RegistryEntry]:
    return er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)


async def test_removal_revokes_the_token(
    hass: HomeAssistant, mock_cloud: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """Deleting the board removes its devices and entities and revokes its token in the cloud."""
    mock_cloud.delete(f"{API}/token", status=204)
    await setup_integration(hass, mock_config_entry)
    assert _entities(hass, mock_config_entry)

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert len(_revokes(mock_cloud, URL, TOKEN)) == 1
    assert not _entities(hass, mock_config_entry)
    assert not dr.async_entries_for_config_entry(dr.async_get(hass), mock_config_entry.entry_id)
    assert not hass.config_entries.async_entries(DOMAIN)


@pytest.mark.parametrize("status", [401, 502])
async def test_removal_without_the_cloud(
    hass: HomeAssistant,
    mock_cloud: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    status: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A token revoked already is fine; an unreachable cloud does not stop the removal but says what to do."""
    mock_cloud.delete(f"{API}/token", status=status)
    await setup_integration(hass, mock_config_entry)

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.config_entries.async_entries(DOMAIN)
    assert ("could not be revoked" in caplog.text) is (status == 502)


async def test_card_leaves_with_the_last_board(
    hass: HomeAssistant, mock_cloud: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """The card loads while a board is set up and stops loading when the last one is deleted; adding one brings it back."""
    mock_cloud.delete(f"{API}/token", status=204)
    hass.config.components.add("frontend")
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    await async_register_card(hass)
    with (
        patch("homeassistant.components.frontend.add_extra_js_url") as add_url,
        patch("homeassistant.components.frontend.remove_extra_js_url") as remove_url,
    ):
        await setup_integration(hass, mock_config_entry)
        await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        assert add_url.call_count == 1
        assert hass.data[CARD].shown

        await hass.config_entries.async_remove(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        remove_url.assert_called_once_with(hass, hass.data[CARD].url)
        assert not hass.data[CARD].shown

        again = MockConfigEntry(domain=DOMAIN, title="Zelt", unique_id="x", data=dict(mock_config_entry.data))
        await setup_integration(hass, again)
        assert add_url.call_count == 2


async def test_new_token_revokes_the_old_one(
    hass: HomeAssistant, mock_cloud: AiohttpClientMocker, mock_config_entry: MockConfigEntry
) -> None:
    """A token replaced through "Reconfigure" is revoked; the board goes on with the new one."""
    mock_cloud.delete(f"{API}/token", status=204)
    await setup_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: URL, CONF_API_TOKEN: NEW_TOKEN}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_API_TOKEN] == NEW_TOKEN
    assert len(_revokes(mock_cloud, URL, TOKEN)) == 1
    assert not _revokes(mock_cloud, URL, NEW_TOKEN)

    # the same token again: nothing to revoke
    result = await mock_config_entry.start_reconfigure_flow(hass)
    await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: URL, CONF_API_TOKEN: NEW_TOKEN})
    await hass.async_block_till_done()
    assert not _revokes(mock_cloud, URL, NEW_TOKEN)


async def test_fewer_rights_remove_the_controls(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
) -> None:
    """After a token that may only read, no switch or setting of the old token stays behind as "unavailable"."""
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    assert {"fan", "number", "select"} <= {entity.domain for entity in _entities(hass, mock_config_entry)}

    board["access"]["canControl"] = False
    board["access"]["canConfigure"] = False
    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json=board)
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    domains = {entity.domain for entity in _entities(hass, mock_config_entry)}
    assert not domains & {"fan", "light", "switch", "valve", "button", "select", "number", "time"}
    assert {"sensor", "binary_sensor", "calendar", "update"} <= domains
    assert all(
        hass.states.get(entity.entity_id) for entity in _entities(hass, mock_config_entry) if not entity.disabled
    )


async def test_deleted_output_disappears(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """An output deleted in the cloud takes its entities with it; one added again comes back."""
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    registry = er.async_get(hass)
    assert registry.async_get("fan.zelt_abluft") is not None

    fan = next(d for d in board["devices"] if d["id"] == FAN)
    without = {**board, "devices": [d for d in board["devices"] if d["id"] != FAN]}
    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json=without)
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert registry.async_get("fan.zelt_abluft") is None
    assert registry.async_get("button.zelt_abluft_automatic") is None
    assert hass.states.get("fan.zelt_abluft") is None

    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json={**board, "devices": [*without["devices"], fan]})
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("fan.zelt_abluft").state == "on"


async def test_co2_stays_while_its_reading_is_missing(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
) -> None:
    """A CO2 sensor without a reading at a restart (cloud just restarted, board offline) keeps its entity and settings."""
    board["areas"][0]["climate"]["co2Ppm"] = 820
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    registry = er.async_get(hass)
    co2 = next(e for e in _entities(hass, mock_config_entry) if e.unique_id == f"{AREA_ID}_co2")
    registry.async_update_entity(co2.entity_id, name="CO₂ Zelt")

    board["areas"][0]["climate"]["co2Ppm"] = None
    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json=board)
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    kept = registry.async_get(co2.entity_id)
    assert kept is not None and kept.name == "CO₂ Zelt"


async def test_moved_plant_keeps_its_entities(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    board: dict[str, Any],
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A plant moved to another grow area keeps its device and entities and shows its values on."""
    aioclient_mock.get(API, json=board)
    await setup_integration(hass, mock_config_entry)
    height = next(e for e in _entities(hass, mock_config_entry) if e.unique_id == f"plant_{PLANT_ID}_height")
    before = hass.states.get(height.entity_id).state

    second = {**board["areas"][0], "id": "ee000000-0000-4000-8000-000000000002", "name": "Schrank"}
    first = {**board["areas"][0], "plantings": []}
    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json={**board, "areas": [first, second]})
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert er.async_get(hass).async_get(height.entity_id) is not None
    assert hass.states.get(height.entity_id).state == before
