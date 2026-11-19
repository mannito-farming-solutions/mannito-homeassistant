"""Sensors of a Mannito board: its sensors, the climate and irrigation of the grow areas, the tank."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    LIGHT_LUX,
    PERCENTAGE,
    EntityCategory,
    UnitOfConductivity,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import Area, BoardSnapshot, Sensor
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import AreaEntity, BoardEntity, MannitoEntity, add_entities_dynamically, bus_device_info

# Sensors only read, the coordinator fetches everything at once
PARALLEL_UPDATES = 0

AREA_STATUS = ["neutral", "ok", "attention", "problem", "nodata"]


@dataclass(frozen=True, kw_only=True)
class AreaSensorDescription(SensorEntityDescription):
    """A value of a grow area."""

    value_fn: Callable[[Area], float | int | str | datetime | None]
    exists_fn: Callable[[Area], bool] = lambda _: True


def _local(value: datetime | None) -> datetime | None:
    """Times of the irrigation are local times of the organization: attach the time zone of Home Assistant."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=dt_util.get_default_time_zone())


AREA_SENSORS: tuple[AreaSensorDescription, ...] = (
    AreaSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda a: a.climate.temperature,
    ),
    AreaSensorDescription(
        key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda a: a.climate.humidity,
    ),
    AreaSensorDescription(
        key="vpd",
        translation_key="vpd",
        native_unit_of_measurement=UnitOfPressure.KPA,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda a: a.climate.vpd,
    ),
    AreaSensorDescription(
        key="leaf_temperature",
        translation_key="leaf_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda a: a.climate.leaf_temperature,
    ),
    AreaSensorDescription(
        key="co2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda a: a.climate.co2,
        exists_fn=lambda a: a.climate.co2 is not None or a.climate.target_co2 is not None,
    ),
    AreaSensorDescription(
        key="intake_temperature",
        translation_key="intake_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=lambda a: a.climate.intake_temperature,
    ),
    AreaSensorDescription(
        key="intake_humidity",
        translation_key="intake_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda a: a.climate.intake_humidity,
    ),
    AreaSensorDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda a: a.climate.target_temperature,
    ),
    AreaSensorDescription(
        key="target_humidity",
        translation_key="target_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda a: a.climate.target_humidity,
    ),
    AreaSensorDescription(
        key="target_vpd",
        translation_key="target_vpd",
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_display_precision=2,
        value_fn=lambda a: a.climate.target_vpd,
    ),
    AreaSensorDescription(
        key="target_co2",
        translation_key="target_co2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda a: a.climate.target_co2,
        exists_fn=lambda a: a.climate.co2 is not None or a.climate.target_co2 is not None,
    ),
    AreaSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=AREA_STATUS,
        value_fn=lambda a: a.status if a.status in AREA_STATUS else None,
    ),
    AreaSensorDescription(
        key="headline",
        translation_key="headline",
        entity_registry_enabled_default=False,
        value_fn=lambda a: a.headline[:255] or None,
    ),
    AreaSensorDescription(
        key="grow_phase",
        translation_key="grow_phase",
        value_fn=lambda a: a.phase.name if a.phase else None,
    ),
    AreaSensorDescription(
        key="day_of_grow",
        translation_key="day_of_grow",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda a: a.phase.day_of_grow if a.phase else None,
    ),
    AreaSensorDescription(
        key="day_of_phase",
        translation_key="day_of_phase",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda a: a.phase.day_of_phase if a.phase else None,
    ),
    AreaSensorDescription(
        key="irrigation_phase",
        translation_key="irrigation_phase",
        value_fn=lambda a: a.irrigation.live.phase if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="substrate_moisture",
        translation_key="substrate_moisture",
        device_class=SensorDeviceClass.MOISTURE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda a: a.irrigation.live.vwc if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="substrate_peak",
        translation_key="substrate_peak",
        device_class=SensorDeviceClass.MOISTURE,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda a: a.irrigation.live.peak_vwc if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="dryback",
        translation_key="dryback",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda a: a.irrigation.live.dryback if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="shots_today",
        translation_key="shots_today",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda a: a.irrigation.live.shots_today if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="water_today",
        translation_key="water_today",
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda a: a.irrigation.live.ml_today if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="last_shot",
        translation_key="last_shot",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda a: _local(a.irrigation.live.last_shot_local) if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="next_shot",
        translation_key="next_shot",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda a: a.irrigation.live.next_shot_min if a.irrigation and a.irrigation.live else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="field_capacity",
        translation_key="field_capacity",
        device_class=SensorDeviceClass.MOISTURE,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda a: a.irrigation.field_capacity if a.irrigation else None,
        exists_fn=lambda a: a.irrigation is not None,
    ),
    AreaSensorDescription(
        key="tank_volume",
        translation_key="tank_volume",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda a: a.tank.liters if a.tank else None,
        exists_fn=lambda a: a.tank is not None,
    ),
    AreaSensorDescription(
        key="tank_level",
        translation_key="tank_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda a: a.tank.percent if a.tank else None,
        exists_fn=lambda a: a.tank is not None,
    ),
)


@dataclass(frozen=True)
class _SensorKind:
    device_class: SensorDeviceClass | None
    unit: str | None


# Reading types of the cloud (ReadingType) -> how Home Assistant shows them
SENSOR_KINDS: dict[str, _SensorKind] = {
    "AIR_TEMPERATURE": _SensorKind(SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    "LEAF_TEMPERATURE": _SensorKind(SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    "HUMIDITY": _SensorKind(SensorDeviceClass.HUMIDITY, PERCENTAGE),
    "CO2": _SensorKind(SensorDeviceClass.CO2, CONCENTRATION_PARTS_PER_MILLION),
    "SOIL_MOISTURE": _SensorKind(SensorDeviceClass.MOISTURE, PERCENTAGE),
    "CONDUCTIVITY": _SensorKind(SensorDeviceClass.CONDUCTIVITY, UnitOfConductivity.MICROSIEMENS_PER_CM),
    "LUX": _SensorKind(SensorDeviceClass.ILLUMINANCE, LIGHT_LUX),
    "PH": _SensorKind(SensorDeviceClass.PH, None),
    "VPD": _SensorKind(None, UnitOfPressure.KPA),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            BoardLastSeenSensor(coordinator),
            BoardSyncPendingSensor(coordinator),
        ]
    )
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: [sensor_id for sensor_id, sensor in coordinator.data.sensors.items() if not sensor.hidden],
        lambda sensor_id: [BoardSensor(coordinator, coordinator.data.sensors[sensor_id])],
    )
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: coordinator.data.areas,
        lambda area_id: [
            AreaSensor(coordinator, coordinator.data.areas[area_id], description)
            for description in AREA_SENSORS
            if description.exists_fn(coordinator.data.areas[area_id])
        ],
    )


class BoardLastSeenSensor(BoardEntity, SensorEntity):
    """When the board last talked to the cloud."""

    _attr_translation_key = "last_seen"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MannitoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "last_seen")

    @property
    def native_value(self) -> datetime | None:
        """Last contact."""
        return self.coordinator.data.board.last_seen


class BoardSyncPendingSensor(BoardEntity, SensorEntity):
    """Changes of the cloud the board did not take over yet."""

    _attr_translation_key = "sync_pending"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: MannitoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "sync_pending")

    @property
    def native_value(self) -> int:
        """Pending changes."""
        return self.coordinator.data.board.sync_pending


class BoardSensor(MannitoEntity, SensorEntity):
    """A sensor of the board or of one of its bus modules, with the name given in the cloud."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: MannitoCoordinator, sensor: Sensor) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        snapshot: BoardSnapshot = coordinator.data
        self.sensor_id = sensor.id
        self._attr_unique_id = f"{snapshot.board.id}_sensor_{sensor.id}"
        self._attr_name = sensor.name
        bus = snapshot.bus_device_of(sensor)
        self._attr_device_info = bus_device_info(coordinator, bus) if bus else self.board_device_info()
        kind = SENSOR_KINDS.get(sensor.type)
        if kind:
            self._attr_device_class = kind.device_class
            self._attr_native_unit_of_measurement = kind.unit
        elif sensor.unit and sensor.unit != "unknown":
            self._attr_native_unit_of_measurement = sensor.unit

    @property
    def available(self) -> bool:
        """Available while the board is online and still has the sensor."""
        return (
            super().available and self.sensor_id in self.coordinator.data.sensors and self.coordinator.data.board.online
        )

    @property
    def native_value(self) -> float | None:
        """Latest value."""
        return self.coordinator.data.sensors[self.sensor_id].value


class AreaSensor(AreaEntity, SensorEntity):
    """A value of a grow area."""

    entity_description: AreaSensorDescription

    def __init__(self, coordinator: MannitoCoordinator, area: Area, description: AreaSensorDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, area, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | str | datetime | None:
        """Current value."""
        return self.entity_description.value_fn(self.area)
