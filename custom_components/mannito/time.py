"""The time the light goes on in a grow area (the grow cycle moves its whole day with it)."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Area
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import AreaEntity, add_entities_dynamically

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lights-on times (tokens with the right to configure, areas with a grow cycle)."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: [
            area_id
            for area_id, area in coordinator.data.areas.items()
            if coordinator.data.access.can_configure and area.phase is not None and area.phase.values is not None
        ],
        lambda area_id: [LightsOnTime(coordinator, coordinator.data.areas[area_id])],
    )


class LightsOnTime(AreaEntity, TimeEntity):
    """When the light goes on (local time of the organization); the night, the irrigation day and the ramps move with it."""

    _attr_translation_key = "lights_on"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: MannitoCoordinator, area: Area) -> None:
        """Initialize the time entity."""
        super().__init__(coordinator, area, "lights_on")

    @property
    def native_value(self) -> time | None:
        """Lights-on time of the grow cycle."""
        phase = self.area.phase
        if phase is None or phase.values is None:
            return None
        hours, minutes = phase.values.lights_on.split(":")
        return time(int(hours), int(minutes))

    @property
    def available(self) -> bool:
        """Available while a grow cycle runs."""
        return super().available and self.area.phase is not None and self.area.phase.values is not None

    async def async_set_value(self, value: time) -> None:
        """Move the lights-on time."""
        await self.async_command(
            self.coordinator.client.async_grow_cycle_action(
                self.area_id, "SetLightsOn", lights_on=value.strftime("%H:%M")
            )
        )
