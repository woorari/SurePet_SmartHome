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


class DeviceTag(SureModel):
    """A pet tag assigned to a flap, with its per-pet permission profile."""

    id: int | None = None
    profile: int | None = None


class CurfewEntry(SureModel):
    """A single curfew window (locked-in between lock and unlock times)."""

    enabled: bool = False
    lock_time: str | None = None
    unlock_time: str | None = None


class BowlSetting(SureModel):
    """A feeder bowl's food type and target weight."""

    food_type: int | None = None
    target: int | None = None


class BowlsControl(SureModel):
    """Feeder bowl configuration."""

    type: int | None = None
    settings: list[BowlSetting] = Field(default_factory=list)


class LidControl(SureModel):
    """Feeder lid configuration."""

    close_delay: int | None = None


class DeviceControl(SureModel):
    """Desired (writable) device state."""

    led_mode: int | None = None
    locking: int | None = None
    curfew: list[CurfewEntry] = Field(default_factory=list)
    bowls: BowlsControl | None = None
    lid: LidControl | None = None
    training_mode: int | None = None


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
    tags: list[DeviceTag] = Field(default_factory=list)

    def tag_profile(self, tag_id: int) -> int | None:
        """The permission profile for a given pet tag on this flap."""
        return next((t.profile for t in self.tags if t.id == tag_id), None)

    @property
    def product_name(self) -> str:
        return PRODUCT_NAMES.get(self.product_id, PRODUCT_NAMES[ProductId.UNKNOWN])

    @property
    def is_flap(self) -> bool:
        return self.product_id in (ProductId.CAT_FLAP, ProductId.PET_FLAP)

    @property
    def is_feeder(self) -> bool:
        return self.product_id in (ProductId.FEEDER, ProductId.FEEDER_LITE)

    @property
    def curfew_active(self) -> bool:
        return self.status.locking is not None and self.status.locking.mode == LockMode.CURFEW

    @property
    def curfew_window(self) -> CurfewEntry | None:
        """The first configured curfew window, if any."""
        return self.control.curfew[0] if self.control.curfew else None
