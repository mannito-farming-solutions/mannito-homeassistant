"""Fans of a Mannito board."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Device
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import OutputEntity, add_entities_dynamically
from .output import FAN_TYPES, outputs_of

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the fans."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: outputs_of(coordinator.data, FAN_TYPES),
        lambda device_id: [MannitoFan(coordinator, coordinator.data.devices[device_id])],
    )


class MannitoFan(OutputEntity, FanEntity):
    """A fan of the board; with a speed when it is a PWM or 0-10 V output."""

    def __init__(self, coordinator: MannitoCoordinator, device: Device) -> None:
        """Initialize the fan."""
        super().__init__(coordinator, device, "fan")
        self._attr_name = device.name
        features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if device.dimmable:
            features |= FanEntityFeature.SET_SPEED
        self._attr_supported_features = features

    @property
    def is_on(self) -> bool:
        """Whether the fan runs."""
        return self.output.on

    @property
    def percentage(self) -> int | None:
        """Speed in percent."""
        if not self.output.dimmable:
            return None
        return (self.output.power_percent or 0) if self.output.on else 0

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        """Switch the fan on (by hand: it leaves the automatic control)."""
        power = max(1, percentage) if percentage and self.output.dimmable else None
        await self.async_switch(True, power_percent=power)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the fan off (by hand)."""
        await self.async_switch(False)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed; 0 switches off."""
        if percentage == 0:
            await self.async_switch(False)
        else:
            await self.async_switch(True, power_percent=percentage)
