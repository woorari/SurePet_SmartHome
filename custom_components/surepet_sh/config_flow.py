"""Config flow for Surepet SmartHome."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from surehub import AuthError, SureHubClient, SureHubError

from .const import CONF_DEVICE_ID, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SurePetSHConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Surepet SmartHome config flow."""

    VERSION = 1

    async def _validate(self, email: str, password: str) -> tuple[str, str]:
        """Log in and return (token, device_id)."""
        client = SureHubClient(session=async_get_clientsession(self.hass))
        token = await client.login(email, password)
        return token, client.device_id

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL]
            try:
                token, device_id = await self._validate(email, user_input[CONF_PASSWORD])
            except AuthError:
                errors["base"] = "invalid_auth"
            except SureHubError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(email.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        # Stored so the integration can silently re-login when
                        # the token expires (kept in HA's config entry storage).
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_TOKEN: token,
                        CONF_DEVICE_ID: device_id,
                    },
                )
        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Handle re-authentication when the token expires."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with a fresh password."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        email = entry.data[CONF_EMAIL]
        if user_input is not None:
            try:
                token, device_id = await self._validate(email, user_input[CONF_PASSWORD])
            except AuthError:
                errors["base"] = "invalid_auth"
            except SureHubError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_TOKEN: token,
                        CONF_DEVICE_ID: device_id,
                    },
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={CONF_EMAIL: email},
            errors=errors,
        )
