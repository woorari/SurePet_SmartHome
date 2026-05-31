"""Pet models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from ..enums import PetLocation
from .base import SureModel


class Photo(SureModel):
    """A pet photo. ``location`` is a public (no-auth) image URL."""

    location: str | None = None


class Position(SureModel):
    """A pet's current location."""

    where: PetLocation = PetLocation.UNKNOWN
    since: datetime | None = None
    device_id: int | None = None


class ConsumptionEvent(SureModel):
    """A feeding or drinking event (latest known)."""

    device_id: int | None = None
    change: list[float] = Field(default_factory=list)
    at: datetime | None = None

    @property
    def total_change(self) -> float | None:
        """Total weight change in grams (negative = consumed)."""
        return round(sum(self.change), 2) if self.change else None


class Pet(SureModel):
    """A pet registered to the household."""

    id: int
    name: str = ""
    species_id: int | None = None
    household_id: int | None = None
    tag_id: int | None = None
    photo: Photo | None = None
    position: Position | None = None
    feeding: ConsumptionEvent | None = None
    drinking: ConsumptionEvent | None = None

    @model_validator(mode="before")
    @classmethod
    def _lift_status(cls, data: Any) -> Any:
        """Lift ``status.{activity,feeding,drinking}`` to top-level fields."""
        if not isinstance(data, dict):
            return data
        status = data.get("status") or {}
        out = dict(data)
        if not out.get("position"):
            out["position"] = data.get("position") or status.get("activity")
        if "feeding" not in out or out["feeding"] is None:
            out["feeding"] = status.get("feeding")
        if "drinking" not in out or out["drinking"] is None:
            out["drinking"] = status.get("drinking")
        return out

    @property
    def is_inside(self) -> bool | None:
        if self.position is None or self.position.where == PetLocation.UNKNOWN:
            return None
        return self.position.where == PetLocation.INSIDE

    @property
    def photo_url(self) -> str | None:
        return self.photo.location if self.photo else None
