"""Household models."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from .base import SureModel


class Timezone(SureModel):
    """Household timezone."""

    timezone: str | None = None
    utc_offset: int | None = None


class HouseholdUser(SureModel):
    """A user's membership of a household (with their permissions)."""

    user_id: int | None = None
    owner: bool = False
    write: bool = False

    @model_validator(mode="before")
    @classmethod
    def _lift_user_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("user"), dict):
            return {**data, "user_id": data["user"].get("id")}
        return data


class Household(SureModel):
    """A Sure Petcare household."""

    id: int
    name: str = ""
    timezone: Timezone | None = None
    users: list[HouseholdUser] = Field(default_factory=list)
