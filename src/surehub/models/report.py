"""Per-pet activity report (movement / feeding / drinking history).

From ``GET /report/household/{household_id}/pet/{pet_id}/aggregate``. Used to
derive daily totals; aggregation methods take a ``since`` datetime (e.g. the
start of the local day) so timezone handling stays with the caller.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from .base import SureModel


class BowlWeight(SureModel):
    """A per-bowl weight change within a feeding/drinking event."""

    index: int | None = None
    weight: float | None = None
    change: float = 0.0
    food_type_id: int | None = None

    @property
    def consumed(self) -> float:
        """Grams consumed (positive). Refills (positive change) count as 0."""
        return -self.change if self.change < 0 else 0.0


class ReportEvent(SureModel):
    """A single movement, feeding or drinking event."""

    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None
    duration: int = 0
    context: int | None = None
    weights: list[BowlWeight] = Field(default_factory=list)

    @property
    def consumed(self) -> float:
        """Total grams consumed across bowls in this event."""
        return round(sum(w.consumed for w in self.weights), 2)


class PetReport(SureModel):
    """Movement / feeding / drinking history for one pet."""

    movement: list[ReportEvent] = Field(default_factory=list)
    feeding: list[ReportEvent] = Field(default_factory=list)
    drinking: list[ReportEvent] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _lift_datapoints(cls, data: object) -> object:
        """Each section is ``{"datapoints": [...]}``; lift to a plain list."""
        if isinstance(data, dict):
            return {
                key: (value.get("datapoints", []) if isinstance(value, dict) else value)
                for key, value in data.items()
            }
        return data

    @staticmethod
    def _since(events: list[ReportEvent], since: datetime) -> list[ReportEvent]:
        return [e for e in events if e.from_ is not None and e.from_ >= since]

    def time_outside(self, since: datetime) -> int:
        """Total seconds spent outside since ``since``."""
        return sum(e.duration for e in self._since(self.movement, since))

    def trips(self, since: datetime) -> int:
        """Number of outdoor trips since ``since``."""
        return len(self._since(self.movement, since))

    def meals(self, since: datetime) -> int:
        """Number of feeds (eating events) since ``since``."""
        return sum(1 for e in self._since(self.feeding, since) if e.consumed > 0)

    def food_eaten(self, since: datetime) -> float:
        """Grams of food eaten since ``since``."""
        return round(sum(e.consumed for e in self._since(self.feeding, since)), 2)

    def drinks(self, since: datetime) -> int:
        """Number of drinking events since ``since``."""
        return sum(1 for e in self._since(self.drinking, since) if e.consumed > 0)

    def water_drunk(self, since: datetime) -> float:
        """Grams of water drunk since ``since``."""
        return round(sum(e.consumed for e in self._since(self.drinking, since)), 2)
