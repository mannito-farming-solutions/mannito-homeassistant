"""Climate control, irrigation mode and dryback strategy of a grow area."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Area, MannitoClient
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import AreaEntity, add_entities_dynamically

PARALLEL_UPDATES = 1

# option of Home Assistant (lowercase translation key) <-> value of the cloud
CLIMATE_CONTROL = {"fuzzy": "FUZZY", "pi": "PI", "mpc": "MPC"}
IRRIGATION_MODE = {"off": "Off", "schedule": "Schedule", "dryback": "Dryback"}
DRYBACK_STRATEGY = {"auto": "Auto", "vegetative": "Vegetative", "generative": "Generative", "custom": "Custom"}


def _option(values: dict[str, str], value: str | None) -> str | None:
    return next((option for option, wire in values.items() if wire == value), None)


@dataclass(frozen=True, kw_only=True)
class AreaSelectDescription(SelectEntityDescription):
    """A choice of a grow area."""

    values: dict[str, str]
    current_fn: Callable[[Area], str | None]
    set_fn: Callable[[MannitoClient, str, str], Awaitable[None]]
    exists_fn: Callable[[Area], bool] = lambda _: True


SELECTS: tuple[AreaSelectDescription, ...] = (
    AreaSelectDescription(
        key="climate_control",
        translation_key="climate_control",
        entity_category=EntityCategory.CONFIG,
        options=list(CLIMATE_CONTROL),
        values=CLIMATE_CONTROL,
        current_fn=lambda a: a.climate_control,
        set_fn=lambda client, area_id, value: client.async_set_climate_control(area_id, value),
    ),
    AreaSelectDescription(
        key="irrigation_mode",
        translation_key="irrigation_mode",
        entity_category=EntityCategory.CONFIG,
        options=list(IRRIGATION_MODE),
        values=IRRIGATION_MODE,
        current_fn=lambda a: a.irrigation.mode if a.irrigation else None,
        set_fn=lambda client, area_id, value: client.async_set_irrigation(area_id, {"mode": value}),
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSelectDescription(
        key="dryback_strategy",
        translation_key="dryback_strategy",
        entity_category=EntityCategory.CONFIG,
        options=list(DRYBACK_STRATEGY),
        values=DRYBACK_STRATEGY,
        current_fn=lambda a: a.irrigation.strategy if a.irrigation else None,
        set_fn=lambda client, area_id, value: client.async_set_irrigation(area_id, {"strategy": value}),
        exists_fn=lambda a: a.irrigation is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the selects (tokens with the right to configure)."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: coordinator.data.areas if coordinator.data.access.can_configure else [],
        lambda area_id: [
            AreaSelect(coordinator, coordinator.data.areas[area_id], description)
            for description in SELECTS
            if description.exists_fn(coordinator.data.areas[area_id])
        ],
    )


class AreaSelect(AreaEntity, SelectEntity):
    """A choice of a grow area."""

    entity_description: AreaSelectDescription

    def __init__(self, coordinator: MannitoCoordinator, area: Area, description: AreaSelectDescription) -> None:
        """Initialize the select."""
        super().__init__(coordinator, area, description.key)
        self.entity_description = description

    @property
    def current_option(self) -> str | None:
        """The chosen option."""
        return _option(self.entity_description.values, self.entity_description.current_fn(self.area))

    async def async_select_option(self, option: str) -> None:
        """Choose an option."""
        await self.async_command(
            self.entity_description.set_fn(
                self.coordinator.client, self.area_id, self.entity_description.values[option]
            )
        )
