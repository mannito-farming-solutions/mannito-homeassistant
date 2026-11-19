"""Serves the Mannito card and loads it on every dashboard."""

from __future__ import annotations

from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN, LOGGER

CARD_URL = f"/{DOMAIN}_static/mannito-card.js"
CARD_FILE = Path(__file__).parent / "frontend" / "mannito-card.js"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card and add it to the frontend (only where Home Assistant runs its web server and frontend)."""
    if hass.http is None or "frontend" not in hass.config.components:
        LOGGER.debug("No frontend: the Mannito card is not registered")
        return
    from homeassistant.components.frontend import add_extra_js_url  # noqa: PLC0415 - only with a frontend
    from homeassistant.components.http import StaticPathConfig  # noqa: PLC0415

    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(CARD_FILE), cache_headers=True)])
    # the version busts the browser cache after an update
    add_extra_js_url(hass, f"{CARD_URL}?v={integration.version}")
