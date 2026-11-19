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
    ATTR_DAYS,
    ATTR_DURATION,
    ATTR_LIGHTS_ON,
    ATTR_ML_PER_POT,
    ATTR_SECONDS,
    ATTR_USE_CO2,
    DOMAIN,
    MAX_VALVE_SECONDS,
    SERVICE_GROW_CYCLE_ACTION,
    SERVICE_OPEN_VALVE,
    SERVICE_RUN_VALVES,
)
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import async_run_command

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


def _area_of(hass: HomeAssistant, device_id: str) -> tuple[MannitoCoordinator, str]:
    """The coordinator and the area id of a grow area device."""
    device = dr.async_get(hass).async_get(device_id)
    area_id = next(
        (
            ident[5:]
            for domain, ident in (device.identifiers if device else ())
            if domain == DOMAIN and ident.startswith("area_")
        ),
        None,
    )
    entry: MannitoConfigEntry | None = hass.config_entries.async_get_entry(device.config_entry_id) if device else None
    if area_id is None or entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_an_area")
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="not_loaded", translation_placeholders={"name": entry.title}
        )
    return entry.runtime_data, area_id


async def _async_run_valves(call: ServiceCall) -> None:
    """Open the valves of a grow area one after another."""
    coordinator, area_id = _area_of(call.hass, call.data[ATTR_AREA])
    await async_run_command(
        coordinator,
        coordinator.client.async_run_valves(
            area_id, seconds=call.data.get(ATTR_SECONDS), ml_per_pot=call.data.get(ATTR_ML_PER_POT)
        ),
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
