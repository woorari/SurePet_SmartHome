"""Household models."""

from __future__ import annotations

from .base import SureModel


class Timezone(SureModel):
    """Household timezone."""

    timezone: str | None = None
    utc_offset: int | None = None


class Household(SureModel):
    """A Sure Petcare household."""

    id: int
    name: str = ""
    timezone: Timezone | None = None
