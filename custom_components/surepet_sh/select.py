"""Select entities for Surepet SmartHome (write/control)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from surehub.enums import HubLedMode, LockMode, ProductId

from .coordinator import SurePetConfigEntry, SurePetCoordinator
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

# Feeder lid close delay (seconds): fast / normal / slow.
CLOSE_DELAY_OPTIONS: dict[str, int] = {"fast": 0, "normal": 4, "slow": 20}
_DELAY_TO_OPTION = {value: option for option, value in CLOSE_DELAY_OPTIONS.items()}

CLOSE_DELAY_SELECT = SelectEntityDescription(
    key="close_delay",
    translation_key="close_delay",
    options=list(CLOSE_DELAY_OPTIONS),
)

# Hub LED brightness.
LED_OPTIONS: dict[str, HubLedMode] = {
    "off": HubLedMode.OFF,
    "high": HubLedMode.HIGH,
    "dimmed": HubLedMode.DIMMED,
}
_LED_TO_OPTION = {mode: option for option, mode in LED_OPTIONS.items()}

LED_MODE_SELECT = SelectEntityDescription(
    key="led_mode",
    translation_key="led_mode",
    entity_category=EntityCategory.CONFIG,
    options=list(LED_OPTIONS),
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
    entities: list[SelectEntity] = []
    for device in account.data.devices:
        if device.is_flap:
            entities.append(SureHubLockModeSelect(account, device.id))
        if device.is_feeder and device.control.lid is not None:
            entities.append(SureHubCloseDelaySelect(account, device.id))
        if device.product_id == ProductId.HUB and device.control.led_mode is not None:
            entities.append(SureHubLedModeSelect(account, device.id))
    async_add_entities(entities)


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


class SureHubCloseDelaySelect(SureHubDeviceEntity, SelectEntity):
    """Feeder lid close delay."""

    def __init__(self, coordinator, device_id: int) -> None:  # noqa: ANN001
        super().__init__(coordinator, device_id, CLOSE_DELAY_SELECT)

    @property
    def current_option(self) -> str | None:
        device = self.device
        if device is None or device.control.lid is None:
            return None
        return _DELAY_TO_OPTION.get(device.control.lid.close_delay)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_device_control(
            self._device_id, {"lid": {"close_delay": CLOSE_DELAY_OPTIONS[option]}}
        )
        await self.coordinator.async_request_refresh()


class SureHubLedModeSelect(SureHubDeviceEntity, SelectEntity):
    """Hub LED brightness."""

    def __init__(self, coordinator: SurePetCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, LED_MODE_SELECT)

    @property
    def current_option(self) -> str | None:
        device = self.device
        if device is None or device.control.led_mode is None:
            return None
        return _LED_TO_OPTION.get(HubLedMode(device.control.led_mode))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_device_control(
            self._device_id, {"led_mode": int(LED_OPTIONS[option])}
        )
        await self.coordinator.async_request_refresh()
