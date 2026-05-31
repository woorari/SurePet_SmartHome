"""Authentication: session management and login."""

from __future__ import annotations

import logging
from uuid import uuid4

import aiohttp

from .const import API_BASE, DEFAULT_HEADERS, DEFAULT_TIMEOUT
from .exceptions import ApiError, AuthError

_LOGGER = logging.getLogger(__name__)


class AuthClient:
    """Holds the aiohttp session, token and device id, and performs login."""

    def __init__(
        self,
        *,
        session: aiohttp.ClientSession | None = None,
        token: str | None = None,
        device_id: str | None = None,
        email: str | None = None,
        password: str | None = None,
        api_base: str = API_BASE,
    ) -> None:
        self._session = session
        self._owns_session = session is None
        self._token = token
        # A stable client UUID; generated once if not supplied.
        self._device_id = device_id or str(uuid4())
        # Optional stored credentials, used to silently re-login when the token
        # expires (so callers are not forced to re-prompt the user).
        self._email = email
        self._password = password
        self._api_base = api_base.rstrip("/")

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def has_credentials(self) -> bool:
        """Whether stored credentials are available for silent re-login."""
        return bool(self._email and self._password)

    async def relogin(self) -> str:
        """Re-login using stored credentials. Raises if none are stored."""
        if not self.has_credentials:
            raise AuthError("No stored credentials to re-login with")
        return await self.login(self._email, self._password)  # type: ignore[arg-type]

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
                headers=DEFAULT_HEADERS,
            )
            self._owns_session = True
        return self._session

    async def login(self, email: str, password: str) -> str:
        """Exchange credentials for a bearer token. Returns the token."""
        session = await self._get_session()
        body = {
            "email_address": email,
            "password": password,
            "device_id": self._device_id,
        }
        async with session.post(f"{self._api_base}/auth/login", json=body) as resp:
            text = await resp.text()
            if resp.status in (400, 401, 403):
                raise AuthError(f"Login failed ({resp.status})")
            if resp.status >= 400:
                raise ApiError(
                    f"Login request failed ({resp.status})",
                    status=resp.status,
                    method="POST",
                    endpoint="/auth/login",
                    payload=text,
                )
            data = await resp.json()
        token = (data or {}).get("data", {}).get("token")
        if not token:
            raise AuthError("Login response did not contain a token")
        self._token = token
        _LOGGER.debug("SureHub login successful")
        return token

    async def close(self) -> None:
        """Close the session if we created it."""
        if self._session is not None and self._owns_session and not self._session.closed:
            await self._session.close()
