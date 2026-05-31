"""Data update coordinators for Surepet SmartHome."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from surehub import (
    Account,
    AuthError,
    AuthExpiredError,
    Notification,
    PetReport,
    SureHubClient,
    SureHubError,
)

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, REPORT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type SurePetConfigEntry = ConfigEntry[SurePetData]


@dataclass
class SurePetData:
    """Runtime data for a config entry: the account and report coordinators."""

    account: SurePetCoordinator
    reports: SurePetReportCoordinator


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
        self.notifications: list[Notification] = []

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
        # Notifications are best-effort; never fail the update over them.
        try:
            self.notifications = await self.client.get_notifications()
        except SureHubError as err:
            _LOGGER.debug("Could not fetch notifications: %s", err)

        self._update_issues(account)
        return account

    def _update_issues(self, account: Account) -> None:
        """Raise/clear repair issues for offline or low-battery devices."""
        for device in account.devices:
            offline_id = f"device_offline_{device.id}"
            if not device.status.online:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    offline_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="device_offline",
                    translation_placeholders={"name": device.name},
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, offline_id)

            battery_id = f"battery_low_{device.id}"
            percentage = device.status.battery_percentage
            if percentage is not None and percentage < 15:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    battery_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="battery_low",
                    translation_placeholders={"name": device.name},
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, battery_id)


class SurePetReportCoordinator(DataUpdateCoordinator[dict[int, PetReport]]):
    """Polls per-pet activity reports, keyed by pet id."""

    config_entry: SurePetConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SurePetConfigEntry,
        client: SureHubClient,
        account: SurePetCoordinator,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_reports",
            update_interval=REPORT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = client
        self._account = account

    async def _async_update_data(self) -> dict[int, PetReport]:
        account = self._account.data
        if account is None:
            return {}
        reports: dict[int, PetReport] = {}
        for pet in account.pets:
            if pet.household_id is None:
                continue
            try:
                reports[pet.id] = await self.client.get_pet_report(pet.household_id, pet.id)
            except (AuthError, AuthExpiredError) as err:
                raise ConfigEntryAuthFailed("Authentication failed") from err
            except SureHubError as err:
                # Don't fail the whole update for one pet's report.
                _LOGGER.warning("Failed to fetch report for pet %s: %s", pet.id, err)
        return reports
