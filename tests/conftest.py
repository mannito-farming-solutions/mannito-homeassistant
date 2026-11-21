"""Fixtures of the Mannito tests."""

from __future__ import annotations

from collections.abc import Generator
import copy
import json
from pathlib import Path
from typing import Any

from homeassistant.const import CONF_API_TOKEN, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.mannito.const import DOMAIN

URL = "https://mannito.example"
TOKEN = "mnt_" + "A" * 43
BOARD_ID = "b0a4d000-0000-4000-8000-000000000001"
AREA_ID = "ee000000-0000-4000-8000-000000000001"
API = f"{URL}/api/v1/board"
PLANTING_ID = "44444444-0000-4000-8000-000000000001"
PLANT_ID = "55555555-0000-4000-8000-000000000003"

BOARD_JSON: dict[str, Any] = json.loads((Path(__file__).parent / "fixtures" / "board.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None]:
    """Load the integration from custom_components."""
    yield


@pytest.fixture
def board() -> dict[str, Any]:
    """A copy of the board answer of the cloud, to change in a test (sensor values are fresh)."""
    data = copy.deepcopy(BOARD_JSON)
    now = dt_util.utcnow().isoformat().replace("+00:00", "Z")
    for sensor in data["sensors"]:
        sensor["valueAtUtc"] = now
    return data


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """A config entry of the board."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Zelt",
        unique_id=BOARD_ID,
        data={CONF_URL: URL, CONF_API_TOKEN: TOKEN},
    )


@pytest.fixture
def mock_cloud(aioclient_mock: AiohttpClientMocker, board: dict[str, Any]) -> AiohttpClientMocker:
    """The board API answering with the board and accepting every command."""
    aioclient_mock.get(API, json=board)
    aioclient_mock.post(
        f"{API}/devices/11111111-0000-4000-8000-000000000001/state", json={"success": True, "message": "ok"}
    )
    aioclient_mock.post(
        f"{API}/devices/11111111-0000-4000-8000-000000000002/state", json={"success": True, "message": "ok"}
    )
    aioclient_mock.post(
        f"{API}/devices/11111111-0000-4000-8000-000000000003/state", json={"success": True, "message": "ok"}
    )
    aioclient_mock.post(
        f"{API}/devices/11111111-0000-4000-8000-000000000004/state", json={"success": True, "message": "ok"}
    )
    aioclient_mock.post(
        f"{API}/devices/11111111-0000-4000-8000-000000000001/automatic", json={"success": True, "message": "ok"}
    )
    aioclient_mock.post(f"{API}/areas/{AREA_ID}/enabled", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/areas/{AREA_ID}/climate-control", json={"success": True, "message": "ok"})
    aioclient_mock.patch(f"{API}/areas/{AREA_ID}/irrigation", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/areas/{AREA_ID}/irrigation/run", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/areas/{AREA_ID}/grow-cycle", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/firmware/update", json={"success": True, "message": "ok"})
    aioclient_mock.patch(f"{API}/areas/{AREA_ID}/phase-values", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/areas/{AREA_ID}/field-capacity", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/areas/{AREA_ID}/tank/entries", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/areas/{AREA_ID}/tank/readings", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/plantings/{PLANTING_ID}/measurements", json={"success": True, "message": "ok"})
    aioclient_mock.post(f"{API}/plantings/{PLANTING_ID}/inspections", json={"success": True, "message": "ok"})
    return aioclient_mock


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Add the entry and set it up."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def calls_to(mock: AiohttpClientMocker, method: str, path: str) -> list[Any]:
    """Bodies of the requests to one endpoint of the board API."""
    return [
        data
        for call_method, url, data, _headers in mock.mock_calls
        if call_method.upper() == method and str(url) == f"{API}{path}"
    ]
