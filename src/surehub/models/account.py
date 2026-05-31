"""The account graph returned by ``GET /me/start``."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ..enums import ProductId
from .base import SureModel
from .device import Device
from .household import Household
from .pet import Pet


class Account(SureModel):
    """Everything the API returns for the logged-in account in one call."""

    user: dict[str, Any] | None = None
    households: list[Household] = Field(default_factory=list)
    devices: list[Device] = Field(default_factory=list)
    pets: list[Pet] = Field(default_factory=list)

    def device(self, device_id: int) -> Device | None:
        return next((d for d in self.devices if d.id == device_id), None)

    def pet(self, pet_id: int) -> Pet | None:
        return next((p for p in self.pets if p.id == pet_id), None)

    @property
    def hub(self) -> Device | None:
        return next((d for d in self.devices if d.product_id == ProductId.HUB), None)
