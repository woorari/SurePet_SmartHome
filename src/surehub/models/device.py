"""Device models."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from ..enums import PRODUCT_NAMES, LockMode, ProductId
from .base import SureModel

# Battery voltage → percentage mapping (≈4×AA): clamp 4.5 V → 0 %, 6.0 V → 100 %.
_BATTERY_MIN_V = 4.5
_BATTERY_MAX_V = 6.0


class Signal(SureModel):
    """Radio signal strength."""

    device_rssi: float | None = None
    hub_rssi: float | None = None


class FirmwareInfo(SureModel):
    """Firmware / hardware versions."""

    hardware: str | None = None
    firmware: str | None = None


class LockingStatus(SureModel):
    """Reported lock state of a flap."""

    mode: LockMode = LockMode.UNKNOWN


class DeviceStatus(SureModel):
    """Reported (read-only) device state."""

    online: bool = False
    battery: float | None = None
    learn_mode: bool | None = None
    signal: Signal | None = None
    locking: LockingStatus | None = None
    version: FirmwareInfo | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten_version(cls, data: Any) -> Any:
        """Lift ``version.device.{firmware,hardware}`` up to ``version``."""
        if isinstance(data, dict):
            version = data.get("version")
            if isinstance(version, dict) and isinstance(version.get("device"), dict):
                data = {**data, "version": version["device"]}
        return data

    @property
    def battery_percentage(self) -> int | None:
        """Approximate battery percentage from raw voltage."""
        if self.battery is None:
            return None
        pct = (self.battery - _BATTERY_MIN_V) / (_BATTERY_MAX_V - _BATTERY_MIN_V) * 100
        return max(0, min(100, round(pct)))


class DeviceControl(SureModel):
    """Desired (writable) device state. Read-only for now; kept loose."""

    led_mode: int | None = None
    locking: int | None = None
    curfew: list[dict[str, Any]] | None = None
    bowls: dict[str, Any] | None = None
    lid: dict[str, Any] | None = None


class Device(SureModel):
    """A Sure Petcare device (hub, flap, feeder, water station, …)."""

    id: int
    product_id: ProductId = ProductId.UNKNOWN
    household_id: int | None = None
    parent_device_id: int | None = None
    name: str = ""
    serial_number: str | None = None
    mac_address: str | None = None
    control: DeviceControl = Field(default_factory=DeviceControl)
    status: DeviceStatus = Field(default_factory=DeviceStatus)

    @property
    def product_name(self) -> str:
        return PRODUCT_NAMES.get(self.product_id, PRODUCT_NAMES[ProductId.UNKNOWN])

    @property
    def is_flap(self) -> bool:
        return self.product_id in (ProductId.CAT_FLAP, ProductId.PET_FLAP)

    @property
    def curfew_active(self) -> bool:
        return self.status.locking is not None and self.status.locking.mode == LockMode.CURFEW
