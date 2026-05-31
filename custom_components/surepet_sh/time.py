"""Time entities for Surepet SmartHome (curfew schedule)."""

from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from surehub.models import CurfewEntry

from .coordinator import SurePetConfigEntry, SurePetCoordinator
from .entity import SureHubDeviceEntity

# This integration manages a single curfew window (index 0). Multiple windows
# (cat flaps support up to 4) are a future enhancement.


def build_curfew(
    window: CurfewEntry | None,
    *,
    enabled: bool | None = None,
    lock_time: str | None = None,
    unlock_time: str | None = None,
) -> list[dict[str, Any]]:
    """Build a one-window curfew payload, preserving unset fields."""
    return [
        {
            "enabled": enabled if enabled is not None else (window.enabled if window else True),
            "lock_time": lock_time
            if lock_time is not None
            else (window.lock_time if window else "00:00"),
            "unlock_time": unlock_time
            if unlock_time is not None
            else (window.unlock_time if window else "00:00"),
        }
    ]


def _parse(hhmm: str | None) -> time | None:
    if not hhmm or ":" not in hhmm:
        return None
    try:
        hour, minute = (int(part) for part in hhmm.split(":")[:2])
        return time(hour, minute)
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up curfew time entities (only for write-capable accounts)."""
    account = entry.runtime_data.account
    if not account.data.can_write:
        return
    entities: list[TimeEntity] = []
    for device in account.data.devices:
        if device.is_flap:
            entities.append(SureHubCurfewTime(account, device.id, "lock"))
            entities.append(SureHubCurfewTime(account, device.id, "unlock"))
    async_add_entities(entities)


class SureHubCurfewTime(SureHubDeviceEntity, TimeEntity):
    """Curfew lock or unlock time for a flap (window 0)."""

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        device_id: int,
        kind: str,
    ) -> None:
        key = "curfew_lock_time" if kind == "lock" else "curfew_unlock_time"
        super().__init__(
            coordinator, device_id, TimeEntityDescription(key=key, translation_key=key)
        )
        self._kind = kind

    @property
    def native_value(self) -> time | None:
        device = self.device
        window = device.curfew_window if device else None
        if window is None:
            return None
        return _parse(window.lock_time if self._kind == "lock" else window.unlock_time)

    async def async_set_value(self, value: time) -> None:
        device = self.device
        if device is None:
            return
        hhmm = value.strftime("%H:%M")
        kwargs = {"lock_time": hhmm} if self._kind == "lock" else {"unlock_time": hhmm}
        payload = build_curfew(device.curfew_window, **kwargs)
        await self.coordinator.client.set_device_control(self._device_id, {"curfew": payload})
        await self.coordinator.async_request_refresh()
