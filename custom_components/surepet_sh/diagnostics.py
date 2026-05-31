"""Diagnostics for Surepet SmartHome."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID
from .coordinator import SurePetConfigEntry

TO_REDACT = {
    CONF_TOKEN,
    CONF_PASSWORD,
    CONF_DEVICE_ID,
    CONF_EMAIL,
    "token",
    "password",
    "device_id",
    "serial_number",
    "mac_address",
    "share_code",
    "location",  # pet photo URLs
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SurePetConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    data = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "account": async_redact_data(data.account.data.model_dump(mode="json"), TO_REDACT),
        "reports": async_redact_data(
            {
                pid: report.model_dump(mode="json")
                for pid, report in (data.reports.data or {}).items()
            },
            TO_REDACT,
        ),
    }
