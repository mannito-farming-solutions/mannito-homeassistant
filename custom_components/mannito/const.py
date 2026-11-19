"""Constants for the Mannito integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "mannito"
LOGGER = logging.getLogger(__package__)

DEFAULT_URL: Final = "https://mannito.de"
SCAN_INTERVAL: Final = timedelta(seconds=30)
REQUEST_TIMEOUT: Final = 20

MANUFACTURER: Final = "Mannito"

# A valve opened from Home Assistant closes again after this many seconds
# (the cloud refuses more than 60 s per opening).
DEFAULT_VALVE_SECONDS: Final = 10
MAX_VALVE_SECONDS: Final = 60

SERVICE_OPEN_VALVE: Final = "open_valve"
SERVICE_RUN_VALVES: Final = "run_valves"
SERVICE_GROW_CYCLE_ACTION: Final = "grow_cycle_action"

ATTR_AREA: Final = "area"
ATTR_DURATION: Final = "duration"
ATTR_SECONDS: Final = "seconds"
ATTR_ML_PER_POT: Final = "ml_per_pot"
ATTR_ACTION: Final = "action"
ATTR_DAYS: Final = "days"
ATTR_LIGHTS_ON: Final = "lights_on"
ATTR_USE_CO2: Final = "use_co2"
