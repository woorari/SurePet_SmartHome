"""Account notification feed."""

from __future__ import annotations

from datetime import datetime

from .base import SureModel


class Notification(SureModel):
    """A single account notification/event entry."""

    id: int | None = None
    type: int | None = None
    text: str = ""
    created_at: datetime | None = None
