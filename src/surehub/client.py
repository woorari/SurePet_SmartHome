"""The SureHub API client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .auth import AuthClient
from .command import Command
from .const import MAX_RETRIES, RETRY_BACKOFF, RETRY_STATUSES
from .exceptions import ApiError, AuthExpiredError
from .models import Account, PetReport

_LOGGER = logging.getLogger(__name__)


class SureHubClient(AuthClient):
    """Async client for the Sure Petcare (SureHub) cloud API."""

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an authenticated request with bounded retries."""
        session = await self._get_session()
        url = endpoint if endpoint.startswith("http") else f"{self._api_base}{endpoint}"

        def _headers() -> dict[str, str]:
            return {"Authorization": f"Bearer {self._token}"} if self._token else {}

        last_exc: Exception | None = None
        relogged = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.request(
                    method, url, params=params, json=json, headers=_headers()
                ) as resp:
                    if resp.status == 401:
                        # Token expired: silently re-login with stored
                        # credentials (once) and retry before giving up.
                        if self.has_credentials and not relogged:
                            await self.relogin()
                            relogged = True
                            continue
                        raise AuthExpiredError("Token rejected (401)")
                    if resp.status in RETRY_STATUSES and attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_BACKOFF * attempt)
                        continue
                    if resp.status >= 400:
                        raise ApiError(
                            f"{method} {endpoint} failed ({resp.status})",
                            status=resp.status,
                            method=method,
                            endpoint=endpoint,
                            payload=await resp.text(),
                        )
                    if resp.content_type == "application/json":
                        return await resp.json()
                    return await resp.text()
            except (TimeoutError, aiohttp.ClientError) as err:
                last_exc = err
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF * attempt)
                    continue
                raise ApiError(
                    f"{method} {endpoint} failed: {err}",
                    method=method,
                    endpoint=endpoint,
                ) from err
        # Exhausted retries on a retryable status.
        raise ApiError(
            f"{method} {endpoint} failed after {MAX_RETRIES} attempts",
            method=method,
            endpoint=endpoint,
        ) from last_exc

    async def api(self, command: Command) -> Any:
        """Run a command, following any chained commands."""
        response = await self._request(
            command.method, command.endpoint, params=command.params, json=command.json
        )
        if command.chain is not None:
            result = command.chain(response)
            commands = result if isinstance(result, list) else [result]
            return [await self.api(c) for c in commands]
        if command.parse is not None:
            return command.parse(response)
        return response

    async def get_account(self) -> Account:
        """Fetch the full account graph (devices, pets, households)."""
        data = await self._request("GET", "/me/start")
        return Account.model_validate((data or {}).get("data", {}))

    async def get_pet_report(self, household_id: int, pet_id: int) -> PetReport:
        """Fetch a pet's movement/feeding/drinking activity report."""
        data = await self._request(
            "GET", f"/report/household/{household_id}/pet/{pet_id}/aggregate"
        )
        return PetReport.model_validate((data or {}).get("data", {}))
