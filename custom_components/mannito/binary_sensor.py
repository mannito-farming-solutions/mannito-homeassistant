"""Binary sensors of a Mannito board: online, day/night, emergency, watering, manual operation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Area, BusDevice, Device
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import AreaEntity, BoardEntity, BusEntity, OutputEntity, add_entities_dynamically

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class AreaBinarySensorDescription(BinarySensorEntityDescription):
    """A yes/no state of a grow area."""

    value_fn: Callable[[Area], bool | None]
    exists_fn: Callable[[Area], bool] = lambda _: True


AREA_BINARY_SENSORS: tuple[AreaBinarySensorDescription, ...] = (
    AreaBinarySensorDescription(
        key="day",
        translation_key="day",
        value_fn=lambda a: a.light.is_day if a.light else None,
    ),
    AreaBinarySensorDescription(
        key="emergency",
        translation_key="emergency",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda a: a.emergency is not None if a.fresh else None,
    ),
    AreaBinarySensorDescription(
        key="watering",
        translation_key="watering",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda a: a.irrigation.live.watering if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities([BoardOnlineSensor(coordinator)])
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: coordinator.data.bus_devices,
        lambda key: [BusOnlineSensor(coordinator, coordinator.data.bus_devices[key])],
    )
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: coordinator.data.areas,
        lambda area_id: [
            AreaBinarySensor(coordinator, coordinator.data.areas[area_id], description)
            for description in AREA_BINARY_SENSORS
            if description.exists_fn(coordinator.data.areas[area_id])
        ],
    )
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: [d.id for d in coordinator.data.devices.values() if not d.hidden],
        lambda device_id: [
            OutputStateSensor(coordinator, coordinator.data.devices[device_id]),
            ManualOverrideSensor(coordinator, coordinator.data.devices[device_id]),
        ],
    )


class BoardOnlineSensor(BoardEntity, BinarySensorEntity):
    """Whether the board is connected to the cloud."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MannitoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "online")

    @property
    def is_on(self) -> bool:
        """Online."""
        return self.coordinator.data.board.online


class BusOnlineSensor(BusEntity, BinarySensorEntity):
    """Whether a bus module answers the board."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MannitoCoordinator, bus: BusDevice) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, bus, "online")

    @property
    def is_on(self) -> bool:
        """Online."""
        return self.bus.online


class AreaBinarySensor(AreaEntity, BinarySensorEntity):
    """A yes/no state of a grow area."""

    entity_description: AreaBinarySensorDescription

    def __init__(self, coordinator: MannitoCoordinator, area: Area, description: AreaBinarySensorDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, area, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Current state."""
        return self.entity_description.value_fn(self.area)


class OutputStateSensor(OutputEntity, BinarySensorEntity):
    """Whether an output is on; for tokens that may only read (the others switch it as light, fan, switch or valve)."""

    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_translation_key = "output_on"

    def __init__(self, coordinator: MannitoCoordinator, device: Device) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device, "on")
        self._attr_translation_placeholders = {"name": device.name}
        self._attr_entity_registry_enabled_default = not coordinator.data.access.can_control

    @property
    def is_on(self) -> bool:
        """On."""
        return self.output.on


class ManualOverrideSensor(OutputEntity, BinarySensorEntity):
    """Whether an output runs by hand instead of under the automatic control."""

    _attr_translation_key = "manual_override"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MannitoCoordinator, device: Device) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device, "manual_override")
        self._attr_translation_placeholders = {"name": device.name}

    @property
    def is_on(self) -> bool:
        """Manual operation."""
        return self.output.manual_override
