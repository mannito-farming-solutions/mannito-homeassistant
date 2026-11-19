"""Diagnostics of the Mannito integration (the token is never included)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant

from .coordinator import MannitoConfigEntry

TO_REDACT = {CONF_API_TOKEN, "token_id", "token_name", "unique_id"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: MannitoConfigEntry) -> dict[str, Any]:
    """Diagnostics of a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "board": async_redact_data(asdict(coordinator.data), TO_REDACT),
    }
