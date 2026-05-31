"""Data update coordinator for Surepet SmartHome."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from surehub import Account, AuthError, AuthExpiredError, SureHubClient, SureHubError

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type SurePetConfigEntry = ConfigEntry[SurePetCoordinator]


class SurePetCoordinator(DataUpdateCoordinator[Account]):
    """Polls the account graph (GET /me/start) for the whole household."""

    config_entry: SurePetConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SurePetConfigEntry,
        client: SureHubClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = client

    async def _async_update_data(self) -> Account:
        try:
            account = await self.client.get_account()
        except AuthError as err:
            # Stored credentials no longer work (e.g. password changed) — this
            # is the only case where we ask the user to re-authenticate.
            raise ConfigEntryAuthFailed("Stored credentials were rejected") from err
        except AuthExpiredError as err:
            # Token expired and no stored credentials to silently re-login.
            raise ConfigEntryAuthFailed("Authentication token expired") from err
        except SureHubError as err:
            raise UpdateFailed(f"Error communicating with Sure Petcare: {err}") from err

        # The client may have silently refreshed the token; persist it.
        if self.client.token and self.client.token != self.config_entry.data.get(CONF_TOKEN):
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, CONF_TOKEN: self.client.token},
            )
        return account
