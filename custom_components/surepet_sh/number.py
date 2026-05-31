"""Number entities for Surepet SmartHome (write/control)."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SurePetConfigEntry, SurePetCoordinator
from .entity import SureHubDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up control numbers (only for write-capable accounts)."""
    account = entry.runtime_data.account
    if not account.data.can_write:
        return
    entities: list[NumberEntity] = []
    for device in account.data.devices:
        if not device.is_feeder or device.control.bowls is None:
            continue
        for index, setting in enumerate(device.control.bowls.settings):
            # Skip unused bowl slots (no food type assigned).
            if setting.food_type:
                entities.append(SureHubBowlTargetNumber(account, device.id, index))
    async_add_entities(entities)


class SureHubBowlTargetNumber(SureHubDeviceEntity, NumberEntity):
    """Target food weight for a feeder bowl."""

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        device_id: int,
        bowl_index: int,
    ) -> None:
        super().__init__(
            coordinator,
            device_id,
            NumberEntityDescription(
                key=f"bowl_target_{bowl_index}",
                translation_key="bowl_target",
                device_class=NumberDeviceClass.WEIGHT,
                native_unit_of_measurement=UnitOfMass.GRAMS,
                native_min_value=0,
                native_max_value=1000,
                native_step=5,
                mode=NumberMode.BOX,
            ),
        )
        self._bowl_index = bowl_index
        self._attr_translation_placeholders = {"bowl": str(bowl_index + 1)}

    @property
    def native_value(self) -> float | None:
        device = self.device
        if device is None or device.control.bowls is None:
            return None
        settings = device.control.bowls.settings
        if self._bowl_index >= len(settings):
            return None
        return settings[self._bowl_index].target

    async def async_set_native_value(self, value: float) -> None:
        device = self.device
        if device is None or device.control.bowls is None:
            return
        bowls = device.control.bowls
        settings = [
            {
                "food_type": setting.food_type,
                "target": int(value) if index == self._bowl_index else setting.target,
            }
            for index, setting in enumerate(bowls.settings)
        ]
        await self.coordinator.client.set_device_control(
            self._device_id, {"bowls": {"type": bowls.type, "settings": settings}}
        )
        await self.coordinator.async_request_refresh()
