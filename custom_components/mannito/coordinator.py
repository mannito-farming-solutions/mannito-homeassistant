"""Polls the board API of the Mannito cloud."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BoardSnapshot, MannitoAuthError, MannitoClient, MannitoError
from .const import DOMAIN, LOGGER, SCAN_INTERVAL

type MannitoConfigEntry = ConfigEntry[MannitoCoordinator]


def board_identifier(board_id: str) -> tuple[str, str]:
    """Device registry identifier of the board."""
    return (DOMAIN, board_id)


def area_identifier(area_id: str) -> tuple[str, str]:
    """Device registry identifier of a grow area."""
    return (DOMAIN, f"area_{area_id}")


def bus_identifier(board_id: str, key: str) -> tuple[str, str]:
    """Device registry identifier of a bus module."""
    return (DOMAIN, f"{board_id}_bus_{key}")


class MannitoCoordinator(DataUpdateCoordinator[BoardSnapshot]):
    """Reads everything about the board every 30 seconds."""

    config_entry: MannitoConfigEntry

    def __init__(self, hass: HomeAssistant, entry: MannitoConfigEntry, client: MannitoClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )
        self.client = client
        # registry id of the board device: parent of the grow areas, via device of the bus modules
        self.board_device_id = ""

    async def _async_update_data(self) -> BoardSnapshot:
        try:
            snapshot = await self.client.async_get_board()
        except MannitoAuthError as err:
            raise ConfigEntryAuthFailed(translation_domain=DOMAIN, translation_key="invalid_auth") from err
        except MannitoError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": err.message},
            ) from err
        self._remove_stale_devices(snapshot)
        return snapshot

    def _remove_stale_devices(self, snapshot: BoardSnapshot) -> None:
        """Remove grow areas and bus modules the board no longer has."""
        current = current_identifiers(snapshot)
        registry = dr.async_get(self.hass)
        entry_id = self.config_entry.entry_id
        devices: list[dr.DeviceEntry | dr.ChildDeviceEntry] = [
            *dr.async_child_entries_for_config_entry(registry, entry_id),
            *dr.async_entries_for_config_entry(registry, entry_id),
        ]
        for device in devices:
            if not device.identifiers & current:
                LOGGER.debug("Removing stale device %s", device.name)
                registry.async_remove_device(device.id)


def current_identifiers(snapshot: BoardSnapshot) -> set[tuple[str, str]]:
    """Registry identifiers of everything the board has now."""
    current = {board_identifier(snapshot.board.id)}
    current |= {area_identifier(area_id) for area_id in snapshot.areas}
    current |= {bus_identifier(snapshot.board.id, key) for key in snapshot.bus_devices}
    return current
