"""Select entities for Surepet SmartHome (write/control)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from surehub.enums import LockMode

from .coordinator import SurePetConfigEntry
from .entity import SureHubDeviceEntity

# Selectable flap lock modes (curfew is an automatic status, not set here).
LOCK_OPTIONS: dict[str, LockMode] = {
    "unlocked": LockMode.UNLOCKED,
    "locked_in": LockMode.LOCKED_IN,
    "locked_out": LockMode.LOCKED_OUT,
    "locked_all": LockMode.LOCKED_ALL,
}
_MODE_TO_OPTION = {mode: option for option, mode in LOCK_OPTIONS.items()}

LOCK_MODE_SELECT = SelectEntityDescription(
    key="lock_mode",
    translation_key="lock_mode",
    options=list(LOCK_OPTIONS),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up control selects (only for write-capable accounts)."""
    account = entry.runtime_data.account
    if not account.data.can_write:
        return
    async_add_entities(
        SureHubLockModeSelect(account, device.id)
        for device in account.data.devices
        if device.is_flap
    )


class SureHubLockModeSelect(SureHubDeviceEntity, SelectEntity):
    """Lock mode of a cat/pet flap."""

    def __init__(self, coordinator, device_id: int) -> None:  # noqa: ANN001
        super().__init__(coordinator, device_id, LOCK_MODE_SELECT)

    @property
    def current_option(self) -> str | None:
        device = self.device
        if device is None or device.status.locking is None:
            return None
        return _MODE_TO_OPTION.get(device.status.locking.mode)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_device_control(
            self._device_id, {"locking": int(LOCK_OPTIONS[option])}
        )
        await self.coordinator.async_request_refresh()
