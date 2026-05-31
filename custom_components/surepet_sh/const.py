"""Constants for the Surepet SmartHome integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "surepet_sh"
MANUFACTURER: Final = "Sure Petcare"

CONF_DEVICE_ID: Final = "device_id"

DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=300)
