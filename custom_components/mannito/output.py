"""Which platform shows which output of the board."""

from __future__ import annotations

from collections.abc import Iterable

from .api import BoardSnapshot

LIGHT_TYPES = frozenset({"light", "dimmer"})
FAN_TYPES = frozenset({"fan"})
VALVE_TYPES = frozenset({"valve"})
SWITCH_TYPES = frozenset({"socket", "relay", "heater", "cooler", "water_pump", "dosing_pump"})


def outputs_of(snapshot: BoardSnapshot, types: frozenset[str]) -> Iterable[str]:
    """Ids of the visible outputs of these types; empty while the token may not switch."""
    if not snapshot.access.can_control:
        return []
    return [d.id for d in snapshot.devices.values() if d.type in types and not d.hidden]


def controllable_outputs(snapshot: BoardSnapshot) -> Iterable[str]:
    """Ids of every visible output; empty while the token may not switch."""
    if not snapshot.access.can_control:
        return []
    return [d.id for d in snapshot.devices.values() if not d.hidden]
