"""Constants for the SureHub client."""

from __future__ import annotations

API_BASE = "https://app-api.production.surehub.io/api"

# The cloud sits behind a WAF that rejects "bot-like" requests, so we present
# headers similar to the official web/mobile clients.
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "SurePetcare/9.0.0 (iPhone; iOS 17.0; Scale/3.00)",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json; charset=utf-8",
    "Origin": "https://surepetcare.io",
    "Referer": "https://surepetcare.io/",
}

DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds, multiplied by attempt number
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
