"""Actions of the Mannito integration."""

from __future__ import annotations

from datetime import time

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr, service
import probatio

from .const import (
    ATTR_ACTION,
    ATTR_AREA,
    ATTR_CONDITION,
    ATTR_DAYS,
    ATTR_DURATION,
    ATTR_EC,
    ATTR_KIND,
    ATTR_LIGHTS_ON,
    ATTR_LITERS,
    ATTR_MEASUREMENT,
    ATTR_ML_PER_POT,
    ATTR_NOTE,
    ATTR_PH,
    ATTR_PROBLEM,
    ATTR_SECONDS,
    ATTR_TARGET,
    ATTR_TEMPERATURE,
    ATTR_USE_CO2,
    ATTR_VALUE,
    DOMAIN,
    MAX_VALVE_SECONDS,
    SERVICE_GROW_CYCLE_ACTION,
    SERVICE_OPEN_VALVE,
    SERVICE_RECORD_MEASUREMENT,
    SERVICE_RECORD_NOTE,
    SERVICE_RUN_VALVES,
    SERVICE_TANK_ENTRY,
    SERVICE_TANK_READING,
)
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import REFRESH_AFTER_SWITCH, async_run_command

# measurement of Home Assistant -> (target of the cloud, factor to its unit): height in cm, the cloud stores mm
MEASUREMENTS: dict[str, tuple[str, float]] = {
    "height": ("PlantHeight", 10.0),
    "stem_thickness": ("StemThickness", 1.0),
    "leaf_size": ("LeafSize", 1.0),
    "plant_weight": ("PlantWeight", 1.0),
    "optic": ("Optic", 1.0),
    "color": ("Color", 1.0),
}
CONDITIONS = {"perfect": "Perfect", "acceptable": "Acceptable", "warning": "Warning", "total_fail": "TotalFail"}
TANK_KINDS = {"fresh": "Fresh", "top_up": "TopUp", "withdrawal": "Withdrawal", "level_check": "LevelCheck"}

RECORD_MEASUREMENT_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_TARGET): cv.string,
        probatio.Required(ATTR_MEASUREMENT): probatio.In(list(MEASUREMENTS)),
        probatio.Required(ATTR_VALUE): probatio.All(probatio.Coerce(float), probatio.Range(min=0, max=100000)),
        probatio.Optional(ATTR_NOTE): probatio.All(cv.string, probatio.Length(max=1000)),
    }
)

RECORD_NOTE_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_TARGET): cv.string,
        probatio.Required(ATTR_CONDITION): probatio.In(list(CONDITIONS)),
        probatio.Optional(ATTR_NOTE): probatio.All(cv.string, probatio.Length(max=1000)),
        probatio.Optional(ATTR_PROBLEM, default=False): cv.boolean,
    }
)

TANK_ENTRY_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_AREA): cv.string,
        probatio.Required(ATTR_KIND): probatio.In(list(TANK_KINDS)),
        probatio.Required(ATTR_LITERS): probatio.All(probatio.Coerce(float), probatio.Range(min=0, max=10000)),
        probatio.Optional(ATTR_NOTE): probatio.All(cv.string, probatio.Length(max=1000)),
    }
)

TANK_READING_SCHEMA = probatio.All(
    probatio.Schema(
        {
            probatio.Required(ATTR_AREA): cv.string,
            probatio.Optional(ATTR_EC): probatio.All(probatio.Coerce(float), probatio.Range(min=0, max=20)),
            probatio.Optional(ATTR_PH): probatio.All(probatio.Coerce(float), probatio.Range(min=0, max=14)),
            probatio.Optional(ATTR_TEMPERATURE): probatio.All(probatio.Coerce(float), probatio.Range(min=-5, max=60)),
        }
    ),
    cv.has_at_least_one_key(ATTR_EC, ATTR_PH, ATTR_TEMPERATURE),
)

# action of Home Assistant -> action of the board API
GROW_CYCLE_ACTIONS = {
    "confirm_phase": "ConfirmPhase",
    "next_phase_now": "NextPhaseNow",
    "postpone": "Postpone",
    "set_lights_on": "SetLightsOn",
    "set_co2": "SetCo2",
}

RUN_VALVES_SCHEMA = probatio.All(
    probatio.Schema(
        {
            probatio.Required(ATTR_AREA): cv.string,
            probatio.Optional(ATTR_SECONDS): probatio.All(
                probatio.Coerce(int), probatio.Range(min=1, max=MAX_VALVE_SECONDS)
            ),
            probatio.Optional(ATTR_ML_PER_POT): probatio.All(probatio.Coerce(int), probatio.Range(min=1, max=1000)),
        }
    ),
    cv.has_at_least_one_key(ATTR_SECONDS, ATTR_ML_PER_POT),
    cv.has_at_most_one_key(ATTR_SECONDS, ATTR_ML_PER_POT),
)

GROW_CYCLE_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_AREA): cv.string,
        probatio.Required(ATTR_ACTION): probatio.In(list(GROW_CYCLE_ACTIONS)),
        probatio.Optional(ATTR_DAYS): probatio.All(probatio.Coerce(int), probatio.Range(min=1, max=14)),
        probatio.Optional(ATTR_LIGHTS_ON): cv.time,
        probatio.Optional(ATTR_USE_CO2): cv.boolean,
    }
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the actions (also while no board is loaded, so automations can be checked)."""
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_OPEN_VALVE,
        entity_domain=Platform.VALVE,
        schema={
            probatio.Required(ATTR_DURATION): probatio.All(
                probatio.Coerce(int), probatio.Range(min=1, max=MAX_VALVE_SECONDS)
            )
        },
        func="async_open_for",
    )
    hass.services.async_register(DOMAIN, SERVICE_RUN_VALVES, _async_run_valves, schema=RUN_VALVES_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_GROW_CYCLE_ACTION, _async_grow_cycle_action, schema=GROW_CYCLE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_RECORD_MEASUREMENT, _async_record_measurement, schema=RECORD_MEASUREMENT_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_RECORD_NOTE, _async_record_note, schema=RECORD_NOTE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TANK_ENTRY, _async_tank_entry, schema=TANK_ENTRY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TANK_READING, _async_tank_reading, schema=TANK_READING_SCHEMA)


def _device_of(hass: HomeAssistant, device_id: str, prefix: str) -> tuple[MannitoCoordinator, str] | None:
    """The coordinator and the id behind a grow area ("area_") or plant ("plant_") device of a loaded board."""
    device = dr.async_get(hass).async_get(device_id)
    found = next(
        (
            ident[len(prefix) :]
            for domain, ident in (device.identifiers if device else ())
            if domain == DOMAIN and ident.startswith(prefix)
        ),
        None,
    )
    entry: MannitoConfigEntry | None = hass.config_entries.async_get_entry(device.config_entry_id) if device else None
    if found is None or entry is None or entry.domain != DOMAIN:
        return None
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="not_loaded", translation_placeholders={"name": entry.title}
        )
    return entry.runtime_data, found


def _area_of(hass: HomeAssistant, device_id: str) -> tuple[MannitoCoordinator, str]:
    """The coordinator and the area id of a grow area device."""
    found = _device_of(hass, device_id, "area_")
    if found is None:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_an_area")
    return found


def _planting_of(hass: HomeAssistant, device_id: str) -> tuple[MannitoCoordinator, str, str | None]:
    """Coordinator, planting and plant (None = the whole planting) of a plant device or of a grow area with one planting."""
    if (plant := _device_of(hass, device_id, "plant_")) is not None:
        coordinator, plant_id = plant
        for area in coordinator.data.areas.values():
            if (found := area.plant(plant_id)) is not None:
                return coordinator, found[0].id, plant_id
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="plant_gone")
    if (area_found := _device_of(hass, device_id, "area_")) is not None:
        coordinator, area_id = area_found
        plantings = coordinator.data.areas[area_id].plantings if area_id in coordinator.data.areas else ()
        if len(plantings) != 1:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="choose_plant")
        return coordinator, plantings[0].id, None
    raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_a_plant")


async def _async_run_valves(call: ServiceCall) -> None:
    """Open the valves of a grow area one after another."""
    coordinator, area_id = _area_of(call.hass, call.data[ATTR_AREA])
    await async_run_command(
        coordinator,
        coordinator.client.async_run_valves(
            area_id, seconds=call.data.get(ATTR_SECONDS), ml_per_pot=call.data.get(ATTR_ML_PER_POT)
        ),
        refresh_after=REFRESH_AFTER_SWITCH,
    )


async def _async_grow_cycle_action(call: ServiceCall) -> None:
    """Steer the running grow cycle of a grow area."""
    coordinator, area_id = _area_of(call.hass, call.data[ATTR_AREA])
    action: str = call.data[ATTR_ACTION]
    if action == "postpone" and ATTR_DAYS not in call.data:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="days_required")
    if action == "set_lights_on" and ATTR_LIGHTS_ON not in call.data:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="lights_on_required")
    if action == "set_co2" and ATTR_USE_CO2 not in call.data:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="use_co2_required")
    lights_on: time | None = call.data.get(ATTR_LIGHTS_ON)
    await async_run_command(
        coordinator,
        coordinator.client.async_grow_cycle_action(
            area_id,
            GROW_CYCLE_ACTIONS[action],
            days=call.data.get(ATTR_DAYS),
            lights_on=lights_on.strftime("%H:%M") if lights_on else None,
            use_co2=call.data.get(ATTR_USE_CO2),
        ),
    )


async def _async_record_measurement(call: ServiceCall) -> None:
    """Record a measurement of a plant (or of the only planting of a grow area)."""
    coordinator, planting_id, plant_id = _planting_of(call.hass, call.data[ATTR_TARGET])
    target, factor = MEASUREMENTS[call.data[ATTR_MEASUREMENT]]
    await async_run_command(
        coordinator,
        coordinator.client.async_record_measurement(
            planting_id,
            target,
            round(call.data[ATTR_VALUE] * factor, 1),
            plant_id=plant_id,
            note=call.data.get(ATTR_NOTE),
        ),
    )


async def _async_record_note(call: ServiceCall) -> None:
    """Record what was seen at a plant (or at the only planting of a grow area)."""
    coordinator, planting_id, plant_id = _planting_of(call.hass, call.data[ATTR_TARGET])
    await async_run_command(
        coordinator,
        coordinator.client.async_record_inspection(
            planting_id,
            CONDITIONS[call.data[ATTR_CONDITION]],
            note=call.data.get(ATTR_NOTE),
            plant_id=plant_id,
            problem=call.data[ATTR_PROBLEM],
        ),
    )


async def _async_tank_entry(call: ServiceCall) -> None:
    """Enter what happened to the tank of a grow area."""
    coordinator, area_id = _area_of(call.hass, call.data[ATTR_AREA])
    await async_run_command(
        coordinator,
        coordinator.client.async_tank_entry(
            area_id, TANK_KINDS[call.data[ATTR_KIND]], call.data[ATTR_LITERS], call.data.get(ATTR_NOTE)
        ),
    )


async def _async_tank_reading(call: ServiceCall) -> None:
    """Record EC, pH or temperature measured in the tank of a grow area."""
    coordinator, area_id = _area_of(call.hass, call.data[ATTR_AREA])
    await async_run_command(
        coordinator,
        coordinator.client.async_tank_reading(
            area_id, ec=call.data.get(ATTR_EC), ph=call.data.get(ATTR_PH), temperature=call.data.get(ATTR_TEMPERATURE)
        ),
    )
