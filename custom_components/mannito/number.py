"""Dryback values and day limits of the irrigation of a grow area.

The values show what the grow area uses now. Changing one switches the dryback
strategy to Custom (starting from the values in use), as on the web page.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Area
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import AreaEntity, add_entities_dynamically

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class IrrigationNumberDescription(NumberEntityDescription):
    """A value of the irrigation; field = its name in the board API."""

    field: str
    integer: bool = True


NUMBERS: tuple[IrrigationNumberDescription, ...] = (
    IrrigationNumberDescription(
        key="p1_start",
        translation_key="p1_start",
        field="p1StartMin",
        native_min_value=0,
        native_max_value=720,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    IrrigationNumberDescription(
        key="p1_shot",
        translation_key="p1_shot",
        field="p1ShotMl",
        native_min_value=0,
        native_max_value=5000,
        native_step=10,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
    ),
    IrrigationNumberDescription(
        key="p1_interval",
        translation_key="p1_interval",
        field="p1IntervalMin",
        native_min_value=5,
        native_max_value=240,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    IrrigationNumberDescription(
        key="p1_max_shots",
        translation_key="p1_max_shots",
        field="p1MaxShots",
        native_min_value=1,
        native_max_value=30,
        native_step=1,
    ),
    IrrigationNumberDescription(
        key="p1_target",
        translation_key="p1_target",
        field="p1TargetVwc",
        integer=False,
        native_min_value=0,
        native_max_value=100,
        native_step=0.1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    IrrigationNumberDescription(
        key="p2_shot",
        translation_key="p2_shot",
        field="p2ShotMl",
        native_min_value=0,
        native_max_value=5000,
        native_step=10,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
    ),
    IrrigationNumberDescription(
        key="p2_dryback",
        translation_key="p2_dryback",
        field="p2DrybackPct",
        integer=False,
        native_min_value=0.5,
        native_max_value=50,
        native_step=0.1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    IrrigationNumberDescription(
        key="p2_min_interval",
        translation_key="p2_min_interval",
        field="p2MinIntervalMin",
        native_min_value=5,
        native_max_value=720,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    IrrigationNumberDescription(
        key="p2_end",
        translation_key="p2_end",
        field="p2EndMin",
        native_min_value=0,
        native_max_value=720,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    IrrigationNumberDescription(
        key="min_vwc",
        translation_key="min_vwc",
        field="minVwc",
        integer=False,
        native_min_value=0,
        native_max_value=100,
        native_step=0.1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    IrrigationNumberDescription(
        key="fallback_interval",
        translation_key="fallback_interval",
        field="fallbackIntervalMin",
        native_min_value=0,
        native_max_value=720,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    IrrigationNumberDescription(
        key="max_day_shots",
        translation_key="max_day_shots",
        field="maxDayShots",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
    ),
    IrrigationNumberDescription(
        key="max_day_ml",
        translation_key="max_day_ml",
        field="maxDayMl",
        native_min_value=0,
        native_max_value=20000,
        native_step=50,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the numbers (tokens with the right to configure, areas with irrigation)."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: [
            area_id
            for area_id, area in coordinator.data.areas.items()
            if coordinator.data.access.can_configure and area.irrigation is not None
        ],
        lambda area_id: [IrrigationNumber(coordinator, coordinator.data.areas[area_id], d) for d in NUMBERS],
    )


class IrrigationNumber(AreaEntity, NumberEntity):
    """A value of the irrigation of a grow area."""

    entity_description: IrrigationNumberDescription
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: MannitoCoordinator, area: Area, description: IrrigationNumberDescription) -> None:
        """Initialize the number."""
        super().__init__(coordinator, area, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        """The value in use."""
        irrigation = self.area.irrigation
        if irrigation is None:
            return None
        if self.entity_description.field == "maxDayShots":
            return irrigation.max_day_shots
        if self.entity_description.field == "maxDayMl":
            return irrigation.max_day_ml
        return irrigation.effective.get(self.entity_description.field)

    async def async_set_native_value(self, value: float) -> None:
        """Change the value."""
        await self.async_command(
            self.coordinator.client.async_set_irrigation(
                self.area_id,
                {self.entity_description.field: round(value) if self.entity_description.integer else round(value, 1)},
            )
        )
