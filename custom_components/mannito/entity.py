"""Base entities of the Mannito integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import replace
from datetime import datetime
from time import monotonic
from typing import Any

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import ChildDeviceInfo, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Area, BusDevice, Device, MannitoError, MannitoForbiddenError, Plant, Planting
from .const import DOMAIN, LOGGER, MANUFACTURER
from .coordinator import (
    MannitoConfigEntry,
    MannitoCoordinator,
    area_identifier,
    board_identifier,
    bus_identifier,
    plant_identifier,
)

# A switched output shows the state it was switched to until the board reports it, at most this long
ASSUME_SECONDS = 20
# The board reports a switched output within a few seconds
REFRESH_AFTER_SWITCH = 4


async def async_run_command(
    coordinator: MannitoCoordinator, command: Awaitable[Any], *, refresh_after: float = 0
) -> None:
    """Run a command against the cloud, translate its errors and refresh (entities and actions).

    Settings are in the cloud at once (refresh right after); a switching command reaches the board first, which reports the new
    state a moment later (refresh_after seconds, the entity shows the expected state meanwhile).
    """
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
    if refresh_after <= 0:
        await coordinator.async_request_refresh()
        return

    @callback
    def _refresh(_now: datetime) -> None:
        coordinator.config_entry.async_create_background_task(
            coordinator.hass, coordinator.async_request_refresh(), "mannito refresh after command"
        )

    coordinator.config_entry.async_on_unload(async_call_later(coordinator.hass, refresh_after, _refresh))


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
        self._assumed: tuple[float, bool, int | None] | None = None

    @property
    def output(self) -> Device:
        """The output as the cloud reported it last, or as it was just switched until the board confirms it."""
        device = self.coordinator.data.devices[self.device_id]
        if self._assumed is None:
            return device
        until, on, power = self._assumed
        confirmed = device.on == on and (power is None or not on or device.power_percent == power)
        if confirmed or monotonic() > until:
            self._assumed = None
            return device
        return replace(device, on=on, power_percent=power if power is not None else device.power_percent)

    async def async_switch(
        self, on: bool, *, power_percent: int | None = None, duration_seconds: int | None = None
    ) -> None:
        """Switch the output by hand; it shows the new state at once and the board confirms it a moment later."""
        await async_run_command(
            self.coordinator,
            self.coordinator.client.async_set_device_state(
                self.device_id, on, power_percent=power_percent, duration_seconds=duration_seconds
            ),
            refresh_after=REFRESH_AFTER_SWITCH,
        )
        seconds = min(duration_seconds, ASSUME_SECONDS) if on and duration_seconds else ASSUME_SECONDS
        self._assumed = (monotonic() + seconds, on, power_percent if on else None)
        self.async_write_ha_state()

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


class PlantEntity(MannitoEntity):
    """An entity of a single plant: a child device of the board named after its area and number."""

    def __init__(self, coordinator: MannitoCoordinator, area: Area, plant: Plant, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.area_id = area.id
        self.plant_id = plant.id
        self._attr_unique_id = f"plant_{plant.id}_{key}"
        self._attr_device_info = ChildDeviceInfo(
            identifiers={plant_identifier(plant.id)},
            name=f"{area.name} {plant.name}",
            parent_device_id=coordinator.board_device_id,
        )

    @property
    def found(self) -> tuple[Planting, Plant] | None:
        """The planting and the plant as the cloud reported them last, in whatever area it stands now (None once harvested)."""
        for area in self.coordinator.data.areas.values():
            if (found := area.plant(self.plant_id)) is not None:
                return found
        return None

    @property
    def available(self) -> bool:
        """Available while the plant grows on this board."""
        return super().available and self.found is not None


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


def add_entities(
    coordinator: MannitoCoordinator, async_add_entities: AddConfigEntryEntitiesCallback, entities: list[Entity]
) -> None:
    """Add entities the board always has."""
    coordinator.provided.update(entity.unique_id for entity in entities if entity.unique_id)
    async_add_entities(entities)


def add_entities_dynamically[K](
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    keys: Callable[[], Iterable[K]],
    build: Callable[[K], Iterable[Entity]],
) -> None:
    """Add the entities of every key now and of every key the board reports later (new outputs, areas, modules, plants).

    The entities of a key the board no longer reports (an output or sensor deleted or hidden in the cloud) are removed.
    """
    coordinator = entry.runtime_data
    built: dict[K, set[str]] = {}

    @callback
    def update() -> None:
        current = list(keys())
        present = set(current)
        gone = [key for key in built if key not in present]
        if gone:
            async_remove_entities(coordinator, {unique_id for key in gone for unique_id in built.pop(key)})
        entities: list[Entity] = []
        for key in current:
            if key in built:
                continue
            made = list(build(key))
            built[key] = {entity.unique_id for entity in made if entity.unique_id}
            coordinator.provided.update(built[key])
            entities.extend(made)
        if entities:
            async_add_entities(entities)

    update()
    entry.async_on_unload(coordinator.async_add_listener(update))


@callback
def async_remove_entities(coordinator: MannitoCoordinator, unique_ids: set[str]) -> None:
    """Remove the entities with these unique ids from Home Assistant: the board no longer has what they show."""
    coordinator.provided -= unique_ids
    registry = er.async_get(coordinator.hass)
    for item in er.async_entries_for_config_entry(registry, coordinator.config_entry.entry_id):
        if item.unique_id in unique_ids:
            LOGGER.debug("Removing %s, the board no longer has it", item.entity_id)
            registry.async_remove(item.entity_id)


@callback
def async_remove_entities_not_provided(coordinator: MannitoCoordinator) -> None:
    """After the setup: remove the entities of this board it no longer provides.

    Outputs or sensors deleted in the cloud while Home Assistant was off, irrigation switched off, or a token with fewer rights
    (switching and configuring entities).
    """
    registry = er.async_get(coordinator.hass)
    stale = {
        item.unique_id
        for item in er.async_entries_for_config_entry(registry, coordinator.config_entry.entry_id)
        if item.unique_id not in coordinator.provided
    }
    if stale:
        async_remove_entities(coordinator, stale)


def command_kwargs(**kwargs: Any) -> dict[str, Any]:
    """Drop the arguments that are None."""
    return {key: value for key, value in kwargs.items() if value is not None}
