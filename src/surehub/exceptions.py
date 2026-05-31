"""Exceptions raised by the SureHub client."""

from __future__ import annotations


class SureHubError(Exception):
    """Base class for all SureHub client errors."""


class ApiError(SureHubError):
    """A non-success HTTP response was returned by the API."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        method: str | None = None,
        endpoint: str | None = None,
        payload: object | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.method = method
        self.endpoint = endpoint
        self.payload = payload


class AuthError(SureHubError):
    """Login failed (e.g. wrong email/password)."""


class AuthExpiredError(SureHubError):
    """The stored token was rejected (HTTP 401); re-authentication is required."""
