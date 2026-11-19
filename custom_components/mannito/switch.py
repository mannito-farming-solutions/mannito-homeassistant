"""Relays and sockets of a Mannito board, and whether a grow area is regulated."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Area, Device
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import AreaEntity, OutputEntity, add_entities_dynamically
from .output import SWITCH_TYPES, outputs_of

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switches."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: outputs_of(coordinator.data, SWITCH_TYPES),
        lambda device_id: [OutputSwitch(coordinator, coordinator.data.devices[device_id])],
    )
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: coordinator.data.areas if coordinator.data.access.can_configure else [],
        lambda area_id: [AreaEnabledSwitch(coordinator, coordinator.data.areas[area_id])],
    )


class OutputSwitch(OutputEntity, SwitchEntity):
    """A relay or socket of the board."""

    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, coordinator: MannitoCoordinator, device: Device) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device, "switch")
        self._attr_name = device.name

    @property
    def is_on(self) -> bool:
        """Whether the output is on."""
        return self.output.on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch on (by hand: it leaves the automatic control)."""
        await self.async_command(self.coordinator.client.async_set_device_state(self.device_id, True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch off (by hand)."""
        await self.async_command(self.coordinator.client.async_set_device_state(self.device_id, False))


class AreaEnabledSwitch(AreaEntity, SwitchEntity):
    """Whether the board regulates the grow area; off switches its devices off, lights too."""

    _attr_translation_key = "control"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: MannitoCoordinator, area: Area) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, area, "control")

    @property
    def is_on(self) -> bool:
        """Whether the area is regulated."""
        return self.area.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Regulate the grow area."""
        await self.async_command(self.coordinator.client.async_set_area_enabled(self.area_id, True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop regulating the grow area."""
        await self.async_command(self.coordinator.client.async_set_area_enabled(self.area_id, False))
