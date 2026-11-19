"""Hand an output of a Mannito board back to the automatic control."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Device
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import OutputEntity, add_entities_dynamically
from .output import controllable_outputs

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the buttons."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: controllable_outputs(coordinator.data),
        lambda device_id: [AutomaticButton(coordinator, coordinator.data.devices[device_id])],
    )


class AutomaticButton(OutputEntity, ButtonEntity):
    """Ends the manual operation of an output: the board controls it again."""

    _attr_translation_key = "automatic"

    def __init__(self, coordinator: MannitoCoordinator, device: Device) -> None:
        """Initialize the button."""
        super().__init__(coordinator, device, "automatic")
        self._attr_translation_placeholders = {"name": device.name}

    async def async_press(self) -> None:
        """Hand the output back to the automatic control."""
        await self.async_command(self.coordinator.client.async_reset_device(self.device_id))
