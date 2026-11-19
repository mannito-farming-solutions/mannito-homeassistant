"""Lamps and 0-10 V dimmer channels of a Mannito board."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.percentage import percentage_to_ranged_value, ranged_value_to_percentage

from .api import Device
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import OutputEntity, add_entities_dynamically
from .output import LIGHT_TYPES, outputs_of

PARALLEL_UPDATES = 1

BRIGHTNESS_SCALE = (1, 255)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lights."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: outputs_of(coordinator.data, LIGHT_TYPES),
        lambda device_id: [MannitoLight(coordinator, coordinator.data.devices[device_id])],
    )


class MannitoLight(OutputEntity, LightEntity):
    """A lamp of the board; dimmable when it has a 0-10 V channel."""

    def __init__(self, coordinator: MannitoCoordinator, device: Device) -> None:
        """Initialize the light."""
        super().__init__(coordinator, device, "light")
        self._attr_name = device.name
        mode = ColorMode.BRIGHTNESS if device.dimmable else ColorMode.ONOFF
        self._attr_color_mode = mode
        self._attr_supported_color_modes = {mode}
        # a bare dimmer channel drives a lamp that has its own entity
        self._attr_entity_registry_enabled_default = device.type != "dimmer"

    @property
    def is_on(self) -> bool:
        """Whether the lamp is on."""
        return self.output.on

    @property
    def brightness(self) -> int | None:
        """Brightness from the power level."""
        level = self.output.power_percent
        if not self.output.dimmable or level is None:
            return None
        return round(percentage_to_ranged_value(BRIGHTNESS_SCALE, level))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch the lamp on (by hand: it leaves the automatic control)."""
        power: int | None = None
        if ATTR_BRIGHTNESS in kwargs and self.output.dimmable:
            power = max(1, ranged_value_to_percentage(BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
        await self.async_command(
            self.coordinator.client.async_set_device_state(self.device_id, True, power_percent=power)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the lamp off (by hand)."""
        await self.async_command(self.coordinator.client.async_set_device_state(self.device_id, False))
