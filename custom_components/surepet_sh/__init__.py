"""The Surepet SmartHome integration."""

from __future__ import annotations

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from surehub import SureHubClient

from .const import CONF_DEVICE_ID
from .coordinator import (
    SurePetConfigEntry,
    SurePetCoordinator,
    SurePetData,
    SurePetReportCoordinator,
)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]


async def async_setup_entry(hass: HomeAssistant, entry: SurePetConfigEntry) -> bool:
    """Set up Surepet SmartHome from a config entry."""
    # Stored credentials let the client silently re-login when the token
    # expires, so the user is not re-prompted unless the password itself fails.
    client = SureHubClient(
        session=async_get_clientsession(hass),
        token=entry.data[CONF_TOKEN],
        device_id=entry.data[CONF_DEVICE_ID],
        email=entry.data.get(CONF_EMAIL),
        password=entry.data.get(CONF_PASSWORD),
    )
    account = SurePetCoordinator(hass, entry, client)
    await account.async_config_entry_first_refresh()

    reports = SurePetReportCoordinator(hass, entry, client, account)
    await reports.async_config_entry_first_refresh()

    entry.runtime_data = SurePetData(account=account, reports=reports)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SurePetConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
