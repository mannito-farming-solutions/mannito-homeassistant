"""Serves the Mannito card and loads it on every dashboard while a board is set up."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from homeassistant.core import HomeAssistant, callback
from homeassistant.loader import async_get_integration
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN, LOGGER

CARD_URL = f"/{DOMAIN}_static/mannito-card.js"
CARD_FILE = Path(__file__).parent / "frontend" / "mannito-card.js"


@dataclass
class Card:
    """The served card: its address with the version (busts the browser cache after an update), loaded on dashboards or not."""

    url: str
    shown: bool = False


CARD: HassKey[Card] = HassKey(f"{DOMAIN}_card")


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card (once per start, only where Home Assistant runs its web server and frontend)."""
    if hass.http is None or "frontend" not in hass.config.components:
        LOGGER.debug("No frontend: the Mannito card is not registered")
        return
    from homeassistant.components.http import StaticPathConfig  # noqa: PLC0415 - only with a frontend

    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(CARD_FILE), cache_headers=True)])
    hass.data[CARD] = Card(f"{CARD_URL}?v={integration.version}")


@callback
def async_show_card(hass: HomeAssistant) -> None:
    """Load the card on every dashboard (a board was set up)."""
    card = hass.data.get(CARD)
    if card is None or card.shown:
        return
    from homeassistant.components.frontend import add_extra_js_url  # noqa: PLC0415 - only with a frontend

    add_extra_js_url(hass, card.url)
    card.shown = True


@callback
def async_hide_card(hass: HomeAssistant) -> None:
    """Stop loading the card (the last board was removed); it is served on until the next start, which does no harm."""
    card = hass.data.get(CARD)
    if card is None or not card.shown:
        return
    from homeassistant.components.frontend import remove_extra_js_url  # noqa: PLC0415 - only with a frontend

    remove_extra_js_url(hass, card.url)
    card.shown = False
