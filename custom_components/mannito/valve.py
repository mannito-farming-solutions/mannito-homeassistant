"""Solenoid valves of a Mannito board: they open only for a short time."""

from __future__ import annotations

from homeassistant.components.valve import ValveDeviceClass, ValveEntity, ValveEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Device
from .const import DEFAULT_VALVE_SECONDS, MAX_VALVE_SECONDS
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import OutputEntity, add_entities_dynamically
from .output import VALVE_TYPES, outputs_of

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the valves."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: outputs_of(coordinator.data, VALVE_TYPES),
        lambda device_id: [MannitoValve(coordinator, coordinator.data.devices[device_id])],
    )


class MannitoValve(OutputEntity, ValveEntity):
    """A solenoid valve. Open closes it again after 10 s; the action mannito.open_valve takes up to 60 s."""

    _attr_device_class = ValveDeviceClass.WATER
    _attr_reports_position = False
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    def __init__(self, coordinator: MannitoCoordinator, device: Device) -> None:
        """Initialize the valve."""
        super().__init__(coordinator, device, "valve")
        self._attr_name = device.name

    @property
    def is_closed(self) -> bool:
        """Whether the valve is closed."""
        return not self.output.on

    async def async_open_valve(self) -> None:
        """Open the valve for a short time."""
        await self.async_open_for(DEFAULT_VALVE_SECONDS)

    async def async_open_for(self, duration: int) -> None:
        """Open the valve for 1-60 seconds."""
        limit = min(self.output.max_on_seconds or MAX_VALVE_SECONDS, MAX_VALVE_SECONDS)
        await self.async_command(
            self.coordinator.client.async_set_device_state(
                self.device_id, True, duration_seconds=max(1, min(int(duration), limit))
            )
        )

    async def async_close_valve(self) -> None:
        """Close the valve."""
        await self.async_command(self.coordinator.client.async_set_device_state(self.device_id, False))
