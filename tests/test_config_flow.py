"""Tests of the config flow."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_TOKEN, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.mannito.const import DOMAIN

from .conftest import API, BOARD_ID, TOKEN, URL

NEW_TOKEN = "mnt_" + "B" * 43


async def test_user_flow(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any]) -> None:
    """A valid token creates the entry of its board."""
    aioclient_mock.get(API, json=board)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: URL + "/", CONF_API_TOKEN: f" {TOKEN} "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Zelt"
    assert result["data"] == {CONF_URL: URL, CONF_API_TOKEN: TOKEN}
    assert result["result"].unique_id == BOARD_ID
    headers = aioclient_mock.mock_calls[-1][3]
    assert headers["Authorization"] == f"Bearer {TOKEN}"


async def test_user_flow_recovers_from_errors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any]
) -> None:
    """A wrong token and an unreachable cloud show an error; a later valid token works."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    aioclient_mock.get(API, status=401)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: URL, CONF_API_TOKEN: TOKEN})
    assert result["errors"] == {"base": "invalid_auth"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(API, status=503)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: URL, CONF_API_TOKEN: TOKEN})
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(API, json=board)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: URL, CONF_API_TOKEN: TOKEN})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_unexpected_error(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """An answer the client cannot read shows unknown."""
    aioclient_mock.get(API, json={"unexpected": True})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: URL, CONF_API_TOKEN: TOKEN})
    assert result["errors"] == {"base": "unknown"}


async def test_board_only_once(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """A board that is set up already is not added twice."""
    mock_config_entry.add_to_hass(hass)
    aioclient_mock.get(API, json=board)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: URL, CONF_API_TOKEN: TOKEN})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """A new token of the same board replaces the old one."""
    mock_config_entry.add_to_hass(hass)
    aioclient_mock.get(API, json=board)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_API_TOKEN: NEW_TOKEN})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_API_TOKEN] == NEW_TOKEN


async def test_reauth_with_token_of_another_board(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """A token of another board is refused."""
    mock_config_entry.add_to_hass(hass)
    board["board"]["id"] = "aaaaaaaa-0000-4000-8000-000000000000"
    aioclient_mock.get(API, json=board)
    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_API_TOKEN: NEW_TOKEN})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_board"
    assert mock_config_entry.data[CONF_API_TOKEN] == TOKEN


async def test_reconfigure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, board: dict[str, Any], mock_config_entry: MockConfigEntry
) -> None:
    """Cloud address and token can be changed."""
    mock_config_entry.add_to_hass(hass)
    other = "https://cloud.example"
    aioclient_mock.get(f"{other}/api/v1/board", json=board)
    aioclient_mock.delete(f"{API}/token", status=204)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    aioclient_mock.get(API, status=401)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: other, CONF_API_TOKEN: NEW_TOKEN}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {CONF_URL: other, CONF_API_TOKEN: NEW_TOKEN}
