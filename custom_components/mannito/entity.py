"""Base entities of the Mannito integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import ChildDeviceInfo, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Area, BusDevice, Device, MannitoError, MannitoForbiddenError
from .const import DOMAIN, MANUFACTURER
from .coordinator import (
    MannitoConfigEntry,
    MannitoCoordinator,
    area_identifier,
    board_identifier,
    bus_identifier,
)


async def async_run_command(coordinator: MannitoCoordinator, command: Awaitable[Any]) -> None:
    """Run a command against the cloud, translate its errors and refresh right after (entities and actions)."""
    try:
        await command
    except MannitoForbiddenError as err:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="missing_right") from err
    except MannitoError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"error": err.message},
        ) from err
    await coordinator.async_request_refresh()


class MannitoEntity(CoordinatorEntity[MannitoCoordinator]):
    """An entity of a Mannito board."""

    _attr_has_entity_name = True

    async def async_command(self, command: Awaitable[Any]) -> None:
        """Run a command against the cloud (see async_run_command)."""
        await async_run_command(self.coordinator, command)

    @property
    def board_id(self) -> str:
        """Id of the board."""
        return self.coordinator.data.board.id

    def board_device_info(self) -> DeviceInfo:
        """The board as a device."""
        board = self.coordinator.data.board
        return DeviceInfo(
            identifiers={board_identifier(board.id)},
            manufacturer=MANUFACTURER,
            model="Mannito Controller",
            name=board.name,
            sw_version=board.firmware,
            configuration_url=f"{self.coordinator.client.url}/CropSteering/Details/{board.id}",
        )


class BoardEntity(MannitoEntity):
    """An entity of the board itself."""

    def __init__(self, coordinator: MannitoCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.board.id}_{key}"
        self._attr_device_info = self.board_device_info()


class OutputEntity(MannitoEntity):
    """An output of the board (relay, fan, lamp, valve)."""

    def __init__(self, coordinator: MannitoCoordinator, device: Device, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device_id = device.id
        self._attr_unique_id = f"{coordinator.data.board.id}_{device.id}_{key}"
        self._attr_device_info = self.board_device_info()

    @property
    def output(self) -> Device:
        """The output as the cloud reported it last."""
        return self.coordinator.data.devices[self.device_id]

    @property
    def available(self) -> bool:
        """Available while the board is online and still has the output."""
        return (
            super().available and self.device_id in self.coordinator.data.devices and self.coordinator.data.board.online
        )


class AreaEntity(MannitoEntity):
    """An entity of a grow area: a child device of the board (a logical part of it, no hardware of its own)."""

    def __init__(self, coordinator: MannitoCoordinator, area: Area, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.area_id = area.id
        self._attr_unique_id = f"{area.id}_{key}"
        self._attr_device_info = ChildDeviceInfo(
            identifiers={area_identifier(area.id)},
            name=area.name,
            parent_device_id=coordinator.board_device_id,
        )

    @property
    def area(self) -> Area:
        """The grow area as the cloud reported it last."""
        return self.coordinator.data.areas[self.area_id]

    @property
    def available(self) -> bool:
        """Available while the board still has the grow area."""
        return super().available and self.area_id in self.coordinator.data.areas


class BusEntity(MannitoEntity):
    """An entity of an RS485 module (its own device below the board)."""

    def __init__(self, coordinator: MannitoCoordinator, bus: BusDevice, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.bus_key = bus.key
        board_id = coordinator.data.board.id
        self._attr_unique_id = f"{board_id}_bus_{bus.key}_{key}"
        self._attr_device_info = bus_device_info(coordinator, bus)

    @property
    def bus(self) -> BusDevice:
        """The module as the cloud reported it last."""
        return self.coordinator.data.bus_devices[self.bus_key]

    @property
    def available(self) -> bool:
        """Available while the board still has the module."""
        return super().available and self.bus_key in self.coordinator.data.bus_devices


def bus_device_info(coordinator: MannitoCoordinator, bus: BusDevice) -> DeviceInfo:
    """A bus module: a product of its own, connected through the board."""
    return DeviceInfo(
        identifiers={bus_identifier(coordinator.data.board.id, bus.key)},
        manufacturer=MANUFACTURER if bus.unique_id else None,
        model=bus.definition,
        name=bus.name,
        sw_version=bus.firmware,
        serial_number=bus.unique_id,
        via_device_id=coordinator.board_device_id,
    )


def add_entities_dynamically[K](
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    keys: Callable[[], Iterable[K]],
    build: Callable[[K], Iterable[Entity]],
) -> None:
    """Add the entities of every key now and of every key the board reports later (new outputs, areas, modules)."""
    known: set[K] = set()

    @callback
    def add_new() -> None:
        new = [key for key in keys() if key not in known]
        if not new:
            return
        known.update(new)
        async_add_entities(entity for key in new for entity in build(key))

    add_new()
    entry.async_on_unload(entry.runtime_data.async_add_listener(add_new))


def command_kwargs(**kwargs: Any) -> dict[str, Any]:
    """Drop the arguments that are None."""
    return {key: value for key, value in kwargs.items() if value is not None}
