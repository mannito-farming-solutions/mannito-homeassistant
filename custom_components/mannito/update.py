"""Firmware of the Mannito board (bus modules are never updated from Home Assistant)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.update import UpdateDeviceClass, UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import BoardEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the firmware update."""
    async_add_entities([FirmwareUpdate(entry.runtime_data)])


class FirmwareUpdate(BoardEntity, UpdateEntity):
    """The firmware of the board; installing needs the right to configure. The board restarts for it."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_translation_key = "firmware"

    def __init__(self, coordinator: MannitoCoordinator) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator, "firmware")
        if coordinator.data.access.can_configure:
            self._attr_supported_features = UpdateEntityFeature.INSTALL

    @property
    def installed_version(self) -> str | None:
        """Installed firmware."""
        firmware = self.coordinator.data.firmware
        return firmware.installed if firmware else self.coordinator.data.board.firmware

    @property
    def latest_version(self) -> str | None:
        """Newest firmware of the release channel of the board."""
        firmware = self.coordinator.data.firmware
        if firmware is None:
            return self.installed_version
        return firmware.available if firmware.update_available and firmware.available else firmware.installed

    @property
    def in_progress(self) -> bool:
        """Whether an update is being installed."""
        firmware = self.coordinator.data.firmware
        return bool(firmware and firmware.update_running)

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Install the newest firmware (the board restarts and is offline for a few minutes)."""
        await self.async_command(self.coordinator.client.async_update_firmware())
