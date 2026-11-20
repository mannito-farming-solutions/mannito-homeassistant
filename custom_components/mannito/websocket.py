"""Websocket command of the Mannito card: the entities of a grow area, found by its device."""

from __future__ import annotations

from typing import Any

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
import probatio

from .const import DOMAIN
from .coordinator import MannitoConfigEntry, plant_identifier

OUTPUT_CONTROLS = ("light", "fan", "switch", "valve")
OUTPUT_KEYS = (*OUTPUT_CONTROLS, "automatic", "on", "manual_override")
BOARD_KEYS = ("online", "last_seen", "sync_pending", "firmware")


@callback
def async_setup_websocket(hass: HomeAssistant) -> None:
    """Register the websocket command."""
    websocket_api.async_register_command(hass, ws_area)


@websocket_api.websocket_command({probatio.Required("type"): "mannito/area", probatio.Required("device_id"): str})
@callback
def ws_area(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Return the grow area of a device with the entity ids the card needs."""
    device = dr.async_get(hass).async_get(msg["device_id"])
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
        connection.send_error(msg["id"], "not_an_area", "Choose a grow area of a Mannito board.")
        return
    if entry.state is not ConfigEntryState.LOADED:
        connection.send_error(msg["id"], "not_loaded", f"The board {entry.title} is not loaded.")
        return
    connection.send_result(msg["id"], area_payload(hass, entry, area_id, msg["device_id"]))


def area_payload(
    hass: HomeAssistant, entry: MannitoConfigEntry, area_id: str, device_id: str | None = None
) -> dict[str, Any]:
    """The grow area, its entities by key, the outputs of the board and the entities of the board."""
    data = entry.runtime_data.data
    board_id = data.board.id
    area = data.areas.get(area_id)
    area_entities: dict[str, str] = {}
    board_entities: dict[str, str] = {}
    output_entities: dict[str, dict[str, str]] = {}
    plant_entities: dict[str, dict[str, str]] = {}
    for item in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id):
        if item.disabled_by is not None:
            continue
        unique_id = item.unique_id
        if unique_id.startswith("plant_") and len(unique_id) > 43:
            plant_entities.setdefault(unique_id[6:42], {})[unique_id[43:]] = item.entity_id
            continue
        if unique_id.startswith(f"{area_id}_"):
            area_entities[unique_id[len(area_id) + 1 :]] = item.entity_id
            continue
        if not unique_id.startswith(f"{board_id}_"):
            continue
        rest = unique_id[len(board_id) + 1 :]
        if rest in BOARD_KEYS:
            board_entities[rest] = item.entity_id
            continue
        for key in OUTPUT_KEYS:
            if rest.endswith(f"_{key}") and rest[: -len(key) - 1] in data.devices:
                output_entities.setdefault(rest[: -len(key) - 1], {})["control" if key in OUTPUT_CONTROLS else key] = (
                    item.entity_id
                )
                break

    assigned = {d.device_id: d for d in area.devices} if area else {}
    outputs = []
    for device in sorted(data.devices.values(), key=lambda d: (d.id not in assigned, d.name.lower())):
        if device.hidden or device.id not in output_entities:
            continue
        function = assigned.get(device.id)
        outputs.append(
            {
                "device_id": device.id,
                "name": device.name,
                "type": device.type,
                "dimmable": device.dimmable,
                "max_on_seconds": device.max_on_seconds,
                "assigned": function is not None,
                "function": function.function if function else None,
                "function_name": function.function_name if function else None,
                "entities": output_entities[device.id],
            }
        )
    devices = dr.async_get(hass)
    plants = []
    for planting in area.plantings if area else ():
        for plant in planting.plants:
            plant_device = devices.async_get_child_device_by_identifier(plant_identifier(plant.id), entry.entry_id)
            plants.append(
                {
                    "plant_id": plant.id,
                    "planting_id": planting.id,
                    "name": plant.name,
                    "variety": planting.variety,
                    "days": planting.days,
                    "device_id": plant_device.id if plant_device else None,
                    "entities": plant_entities.get(plant.id, {}),
                }
            )
    return {
        "area_id": area_id,
        "area_device_id": device_id,
        "name": area.name if area else None,
        "board": data.board.name,
        "can_control": data.access.can_control,
        "can_configure": data.access.can_configure,
        "entities": area_entities,
        "board_entities": board_entities,
        "outputs": outputs,
        "plants": plants,
    }
