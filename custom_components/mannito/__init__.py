"""The Mannito integration: a Mannito grow controller through the Mannito cloud."""

from __future__ import annotations

from homeassistant.const import CONF_API_TOKEN, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import MannitoClient
from .const import DOMAIN, MANUFACTURER
from .coordinator import MannitoConfigEntry, MannitoCoordinator, board_identifier, current_identifiers
from .frontend import async_register_card
from .services import async_setup_services
from .websocket import async_setup_websocket

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.FAN,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
    Platform.VALVE,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the actions, the websocket command and the card of the integration."""
    async_setup_services(hass)
    async_setup_websocket(hass)
    await async_register_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MannitoConfigEntry) -> bool:
    """Set up a Mannito board from a config entry."""
    client = MannitoClient(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_TOKEN])
    coordinator = MannitoCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    board = coordinator.data.board
    # the board first: the grow areas (child devices) and bus modules (via the board) refer to its registry id
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={board_identifier(board.id)},
        manufacturer=MANUFACTURER,
        model="Mannito Controller",
        name=board.name,
        sw_version=board.firmware,
        configuration_url=f"{client.url}/CropSteering/Details/{board.id}",
    )
    coordinator.board_device_id = device.id
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MannitoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: MannitoConfigEntry, device: dr.DeviceEntry | dr.ChildDeviceEntry
) -> bool:
    """Allow removing a grow area or bus module the board no longer has."""
    return not device.identifiers & current_identifiers(entry.runtime_data.data)
