"""The grow phases of a grow area as a calendar (done, current and planned phases)."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Area, PhaseSpan
from .coordinator import MannitoConfigEntry, MannitoCoordinator
from .entity import AreaEntity, add_entities_dynamically

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MannitoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the calendars."""
    coordinator = entry.runtime_data
    add_entities_dynamically(
        entry,
        async_add_entities,
        lambda: coordinator.data.areas,
        lambda area_id: [GrowCalendar(coordinator, coordinator.data.areas[area_id])],
    )


def _event(span: PhaseSpan) -> CalendarEvent | None:
    if span.start is None:
        return None
    end = span.end if span.end and span.end > span.start else span.start + timedelta(days=max(span.planned_days, 1))
    state = "done" if span.done else "current" if span.current else "planned"
    return CalendarEvent(
        start=span.start,
        end=end,
        summary=span.name,
        description=f"{span.kind} · {state}",
        uid=f"{span.kind}-{span.start.isoformat()}",
    )


class GrowCalendar(AreaEntity, CalendarEntity):
    """The phases of the running grow cycle: what came, what runs now and what is planned."""

    _attr_translation_key = "grow_phases"

    def __init__(self, coordinator: MannitoCoordinator, area: Area) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator, area, "grow_phases")

    def _events(self) -> list[CalendarEvent]:
        phase = self.area.phase
        if phase is None:
            return []
        return [event for event in (_event(span) for span in phase.timeline) if event is not None]

    @property
    def event(self) -> CalendarEvent | None:
        """The current phase, else the next one."""
        phase = self.area.phase
        if phase is None:
            return None
        current = next((span for span in phase.timeline if span.current), None)
        if current is not None and (event := _event(current)) is not None:
            return event
        upcoming = sorted(
            (e for e in self._events() if e.start_datetime_local >= datetime.now(tz=e.start_datetime_local.tzinfo)),
            key=lambda e: e.start_datetime_local,
        )
        return upcoming[0] if upcoming else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """The phases that overlap the range."""
        return [e for e in self._events() if e.end_datetime_local > start_date and e.start_datetime_local < end_date]
