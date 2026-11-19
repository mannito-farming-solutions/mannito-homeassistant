"""Asynchronous client for the Mannito board API (``/api/v1/board``).

An API token belongs to one Mannito board (controller). It is created in the
Mannito cloud on the page of the board under "API-Zugänge" and sent as
``Authorization: Bearer mnt_…``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self

from aiohttp import ClientError, ClientResponse, ClientSession

from .const import REQUEST_TIMEOUT

type JsonObject = dict[str, Any]


class MannitoError(Exception):
    """Base error of the Mannito client."""

    def __init__(self, message: str = "") -> None:
        """Initialize the error with the message of the cloud."""
        super().__init__(message)
        self.message = message


class MannitoConnectionError(MannitoError):
    """The cloud could not be reached or answered with a server error."""


class MannitoAuthError(MannitoError):
    """The token is unknown, revoked or expired (HTTP 401)."""


class MannitoForbiddenError(MannitoError):
    """The token lacks the right for this request (HTTP 403)."""


class MannitoRequestError(MannitoError):
    """The cloud refused the request (HTTP 400, 404 or 409) with a reason."""


def _dt(value: Any) -> datetime | None:
    """Parse an ISO timestamp of the cloud (UTC values end with Z)."""
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _float(value: Any) -> float | None:
    return None if value is None else float(value)


def _int(value: Any) -> int | None:
    return None if value is None else int(value)


@dataclass(frozen=True, slots=True)
class BoardInfo:
    """The board (controller)."""

    id: str
    name: str
    online: bool
    firmware: str | None
    last_seen: datetime | None
    sync: str
    sync_pending: int
    sync_problems: int

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            id=data["id"],
            name=data["name"],
            online=bool(data["online"]),
            firmware=data.get("firmware"),
            last_seen=_dt(data.get("lastSeenUtc")),
            sync=data.get("sync", "unknown"),
            sync_pending=int(data.get("syncPending", 0)),
            sync_problems=int(data.get("syncProblems", 0)),
        )


@dataclass(frozen=True, slots=True)
class Access:
    """What the token may do."""

    token_id: str
    token_name: str
    can_control: bool
    can_configure: bool
    expires_at: datetime | None

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            token_id=data["tokenId"],
            token_name=data.get("tokenName", ""),
            can_control=bool(data["canControl"]),
            can_configure=bool(data["canConfigure"]),
            expires_at=_dt(data.get("expiresAtUtc")),
        )


@dataclass(frozen=True, slots=True)
class Firmware:
    """Firmware of the board."""

    installed: str | None
    channel: str
    available: str | None
    update_available: bool
    update_running: bool

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            installed=data.get("installed"),
            channel=data.get("channel", "production"),
            available=data.get("available"),
            update_available=bool(data.get("updateAvailable", False)),
            update_running=bool(data.get("updateRunning", False)),
        )


@dataclass(frozen=True, slots=True)
class Device:
    """An output of the board (relay, fan, lamp, valve …)."""

    id: str
    name: str
    identifier: str
    type: str
    kind: str
    on: bool
    power_percent: int | None
    dimmable: bool
    manual_override: bool
    hidden: bool
    max_on_seconds: int | None

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            id=data["id"],
            name=data["name"],
            identifier=data["identifier"],
            type=data["type"],
            kind=data.get("kind", ""),
            on=bool(data["on"]),
            power_percent=_int(data.get("powerPercent")),
            dimmable=bool(data.get("dimmable", False)),
            manual_override=bool(data.get("manualOverride", False)),
            hidden=bool(data.get("hidden", False)),
            max_on_seconds=_int(data.get("maxOnSeconds")),
        )


@dataclass(frozen=True, slots=True)
class Sensor:
    """A sensor of the board with its latest value."""

    id: str
    name: str
    identifier: str
    type: str
    unit: str | None
    value: float | None
    value_at: datetime | None
    hidden: bool

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            id=data["id"],
            name=data["name"],
            identifier=data["identifier"],
            type=data["type"],
            unit=data.get("unit"),
            value=_float(data.get("value")),
            value_at=_dt(data.get("valueAtUtc")),
            hidden=bool(data.get("hidden", False)),
        )


@dataclass(frozen=True, slots=True)
class BusDevice:
    """An RS485 module of the board (Mannito VPD module, HaliSense probe …)."""

    address: int | None
    definition: str
    unique_id: str | None
    firmware: str | None
    online: bool
    name: str
    sensors: tuple[str, ...]
    state: str | None

    @property
    def key(self) -> str:
        """Stable key: the unique id of a Mannito module, else its address."""
        return self.unique_id or f"address_{self.address}"

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            address=_int(data.get("address")),
            definition=data.get("definition", ""),
            unique_id=data.get("uniqueId"),
            firmware=data.get("firmware"),
            online=bool(data.get("online", False)),
            name=data.get("name") or data.get("definition", ""),
            sensors=tuple(data.get("sensors") or ()),
            state=data.get("state"),
        )


@dataclass(frozen=True, slots=True)
class Climate:
    """Climate of a grow area as measured and targeted by the board."""

    temperature: float | None
    humidity: float | None
    vpd: float | None
    co2: float | None
    leaf_temperature: float | None
    intake_temperature: float | None
    intake_humidity: float | None
    target_temperature: float | None
    target_humidity: float | None
    target_vpd: float | None
    target_co2: float | None

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            temperature=_float(data.get("temperatureC")),
            humidity=_float(data.get("humidityPct")),
            vpd=_float(data.get("vpdKpa")),
            co2=_float(data.get("co2Ppm")),
            leaf_temperature=_float(data.get("leafTemperatureC")),
            intake_temperature=_float(data.get("intakeTemperatureC")),
            intake_humidity=_float(data.get("intakeHumidityPct")),
            target_temperature=_float(data.get("targetTemperatureC")),
            target_humidity=_float(data.get("targetHumidityPct")),
            target_vpd=_float(data.get("targetVpdKpa")),
            target_co2=_float(data.get("targetCo2Ppm")),
        )


@dataclass(frozen=True, slots=True)
class Light:
    """Light of a grow area."""

    is_day: bool
    on: bool
    headline: str
    next_change: str | None
    lights_on: str | None
    lights_off: str | None

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            is_day=bool(data.get("isDay", False)),
            on=bool(data.get("on", False)),
            headline=data.get("headline", ""),
            next_change=data.get("nextChange"),
            lights_on=data.get("lightsOn"),
            lights_off=data.get("lightsOff"),
        )


@dataclass(frozen=True, slots=True)
class Phase:
    """The running grow cycle of a grow area."""

    cycle_id: str
    name: str
    kind: str
    day_of_grow: int
    day_of_phase: int
    planned_days: int
    progress: str
    next: str | None
    confirm_required: bool

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            cycle_id=data["cycleId"],
            name=data["name"],
            kind=data.get("kind", ""),
            day_of_grow=int(data.get("dayOfGrow", 0)),
            day_of_phase=int(data.get("dayOfPhase", 0)),
            planned_days=int(data.get("plannedDays", 0)),
            progress=data.get("progress", ""),
            next=data.get("next"),
            confirm_required=bool(data.get("confirmRequired", False)),
        )


# JSON keys of the dryback values (DrybackValues of the cloud)
DRYBACK_KEYS: tuple[str, ...] = (
    "p1StartMin",
    "p1ShotMl",
    "p1IntervalMin",
    "p1MaxShots",
    "p1TargetVwc",
    "p2ShotMl",
    "p2DrybackPct",
    "p2MinIntervalMin",
    "p2EndMin",
    "minVwc",
    "fallbackIntervalMin",
)


@dataclass(frozen=True, slots=True)
class IrrigationLive:
    """What the irrigation of a grow area does now."""

    phase: str | None
    phase_text: str | None
    vwc: float | None
    peak_vwc: float | None
    dryback: float | None
    shots_today: int
    ml_today: int
    watering: bool
    last_shot_local: datetime | None
    next_shot_min: int | None
    hold_text: str | None
    fresh: bool

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            phase=data.get("phase"),
            phase_text=data.get("phaseText"),
            vwc=_float(data.get("vwcPct")),
            peak_vwc=_float(data.get("peakVwcPct")),
            dryback=_float(data.get("drybackPct")),
            shots_today=int(data.get("shotsToday", 0)),
            ml_today=int(data.get("mlToday", 0)),
            watering=bool(data.get("watering", False)),
            last_shot_local=_dt(data.get("lastShotLocal")),
            next_shot_min=_int(data.get("nextShotMin")),
            hold_text=data.get("holdText"),
            fresh=bool(data.get("fresh", False)),
        )


@dataclass(frozen=True, slots=True)
class Irrigation:
    """Irrigation of a grow area: settings, values in use and live state."""

    mode: str
    strategy: str
    effective_strategy: str
    effective: dict[str, float]
    max_day_shots: int
    max_day_ml: int
    field_capacity: float | None
    valves: int
    live: IrrigationLive | None
    problems: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        effective = data.get("effective") or {}
        return cls(
            mode=data["mode"],
            strategy=data["strategy"],
            effective_strategy=str(data.get("effectiveStrategy") or data["strategy"]),
            effective={key: float(effective[key]) for key in DRYBACK_KEYS if effective.get(key) is not None},
            max_day_shots=int(data.get("maxDayShots", 0)),
            max_day_ml=int(data.get("maxDayMl", 0)),
            field_capacity=_float(data.get("fieldCapacityPct")),
            valves=int(data.get("valves", 0)),
            live=IrrigationLive.from_dict(data["live"]) if data.get("live") else None,
            problems=tuple(data.get("problems") or ()),
        )


@dataclass(frozen=True, slots=True)
class Tank:
    """The water tank a grow area draws from (level worked out by the cloud)."""

    id: str
    name: str
    liters: float | None
    capacity_liters: float | None
    percent: int | None

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            id=data["id"],
            name=data["name"],
            liters=_float(data.get("liters")),
            capacity_liters=_float(data.get("capacityLiters")),
            percent=_int(data.get("percent")),
        )


@dataclass(frozen=True, slots=True)
class AreaDevice:
    """An output of the board assigned to a grow area, with its function there."""

    device_id: str
    function: str
    function_name: str

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            device_id=data["deviceId"],
            function=data.get("function", ""),
            function_name=data.get("functionName") or data.get("function", ""),
        )


@dataclass(frozen=True, slots=True)
class Area:
    """A grow area (slot) of the board."""

    id: str
    name: str
    place: int | None
    enabled: bool
    fresh: bool
    data_at: datetime | None
    status: str
    headline: str
    emergency: str | None
    climate_control: str
    active_control: str | None
    climate: Climate
    light: Light | None
    phase: Phase | None
    irrigation: Irrigation | None
    tank: Tank | None
    warnings: tuple[str, ...]
    devices: tuple[AreaDevice, ...] = ()

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        return cls(
            id=data["id"],
            name=data["name"],
            place=_int(data.get("place")),
            enabled=bool(data.get("enabled", False)),
            fresh=bool(data.get("fresh", False)),
            data_at=_dt(data.get("dataAtUtc")),
            status=data.get("status", "nodata"),
            headline=data.get("headline", ""),
            emergency=data.get("emergency"),
            climate_control=data.get("climateControl", "FUZZY"),
            active_control=data.get("activeControl"),
            climate=Climate.from_dict(data.get("climate") or {}),
            light=Light.from_dict(data["light"]) if data.get("light") else None,
            phase=Phase.from_dict(data["phase"]) if data.get("phase") else None,
            irrigation=Irrigation.from_dict(data["irrigation"]) if data.get("irrigation") else None,
            tank=Tank.from_dict(data["tank"]) if data.get("tank") else None,
            warnings=tuple(w.get("title", "") for w in data.get("warnings") or ()),
            devices=tuple(AreaDevice.from_dict(item) for item in data.get("devices") or ()),
        )


@dataclass(frozen=True, slots=True)
class BoardSnapshot:
    """Everything the cloud knows about the board of the token."""

    board: BoardInfo
    access: Access
    firmware: Firmware | None
    devices: dict[str, Device]
    sensors: dict[str, Sensor]
    bus_devices: dict[str, BusDevice]
    areas: dict[str, Area]

    @classmethod
    def from_dict(cls, data: JsonObject) -> Self:
        """Create from the JSON of the cloud."""
        bus = [BusDevice.from_dict(item) for item in data.get("busDevices") or ()]
        return cls(
            board=BoardInfo.from_dict(data["board"]),
            access=Access.from_dict(data["access"]),
            firmware=Firmware.from_dict(data["firmware"]) if data.get("firmware") else None,
            devices={d.id: d for d in (Device.from_dict(item) for item in data.get("devices") or ())},
            sensors={s.id: s for s in (Sensor.from_dict(item) for item in data.get("sensors") or ())},
            bus_devices={b.key: b for b in bus},
            areas={a.id: a for a in (Area.from_dict(item) for item in data.get("areas") or ())},
        )

    def bus_device_of(self, sensor: Sensor) -> BusDevice | None:
        """The bus module a sensor belongs to, None for sensors of the board itself."""
        for bus in self.bus_devices.values():
            if sensor.identifier in bus.sensors:
                return bus
        return None


class MannitoClient:
    """Client of the board API, bound to the board of its token."""

    def __init__(self, session: ClientSession, url: str, token: str) -> None:
        """Initialize the client with the websession of Home Assistant."""
        self._session = session
        self.url = url.rstrip("/")
        self._base = self.url + "/api/v1/board"
        self._token = token

    async def async_get_board(self) -> BoardSnapshot:
        """Read everything about the board."""
        return BoardSnapshot.from_dict(await self._request("GET", ""))

    async def async_set_device_state(
        self,
        device_id: str,
        on: bool,
        *,
        power_percent: int | None = None,
        duration_seconds: int | None = None,
    ) -> None:
        """Switch an output by hand (it leaves the automatic control)."""
        body: JsonObject = {"on": on}
        if power_percent is not None:
            body["powerPercent"] = power_percent
        if duration_seconds is not None:
            body["durationSeconds"] = duration_seconds
        await self._request("POST", f"/devices/{device_id}/state", body)

    async def async_reset_device(self, device_id: str) -> None:
        """Hand an output back to the automatic control."""
        await self._request("POST", f"/devices/{device_id}/automatic", {})

    async def async_set_area_enabled(self, area_id: str, enabled: bool) -> None:
        """Switch the control of a grow area on or off."""
        await self._request("POST", f"/areas/{area_id}/enabled", {"enabled": enabled})

    async def async_set_climate_control(self, area_id: str, mode: str) -> None:
        """Choose the climate control of a grow area: FUZZY, PI or MPC."""
        await self._request("POST", f"/areas/{area_id}/climate-control", {"mode": mode})

    async def async_set_irrigation(self, area_id: str, changes: JsonObject) -> None:
        """Change the irrigation of a grow area; only the given values change."""
        await self._request("PATCH", f"/areas/{area_id}/irrigation", changes)

    async def async_run_valves(
        self, area_id: str, *, seconds: int | None = None, ml_per_pot: int | None = None
    ) -> None:
        """Open the valves of a grow area one after another (at most 60 s each)."""
        await self._request("POST", f"/areas/{area_id}/irrigation/run", {"seconds": seconds, "mlPerPot": ml_per_pot})

    async def async_grow_cycle_action(
        self,
        area_id: str,
        action: str,
        *,
        days: int | None = None,
        lights_on: str | None = None,
        use_co2: bool | None = None,
    ) -> None:
        """Steer the running grow cycle of a grow area."""
        await self._request(
            "POST",
            f"/areas/{area_id}/grow-cycle",
            {"action": action, "days": days, "lightsOn": lights_on, "useCo2": use_co2},
        )

    async def async_update_firmware(self) -> None:
        """Install the newest firmware on the board (it restarts)."""
        await self._request("POST", "/firmware/update", {"force": False})

    async def _request(self, method: str, path: str, body: JsonObject | None = None) -> JsonObject:
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.request(method, self._base + path, json=body, headers=headers)
                return await self._read(response)
        except TimeoutError as err:
            raise MannitoConnectionError("timeout") from err
        except ClientError as err:
            raise MannitoConnectionError(str(err)) from err

    @staticmethod
    async def _read(response: ClientResponse) -> JsonObject:
        async with response:
            if response.status == 401:
                raise MannitoAuthError("unauthorized")
            if response.status == 403:
                raise MannitoForbiddenError("forbidden")
            if response.status >= 500:
                raise MannitoConnectionError(f"HTTP {response.status}")
            if response.status >= 400:
                detail = ""
                if response.content_type.endswith("json"):
                    problem = await response.json()
                    detail = str(problem.get("detail") or problem.get("title") or "")
                raise MannitoRequestError(detail or f"HTTP {response.status}")
            data = await response.json()
            if not isinstance(data, dict):
                raise MannitoConnectionError("unexpected answer")
            return data
