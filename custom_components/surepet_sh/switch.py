"""Switch entities for Surepet SmartHome (write/control)."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from surehub.enums import PetProfile

from .coordinator import SurePetConfigEntry, SurePetCoordinator
from .entity import SureHubDeviceEntity
from .time import build_curfew


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up control switches (only for write-capable accounts)."""
    account = entry.runtime_data.account
    if not account.data.can_write:
        return
    pet_name = {pet.tag_id: pet.name for pet in account.data.pets if pet.tag_id is not None}
    entities: list[SwitchEntity] = []
    for device in account.data.devices:
        if not device.is_flap:
            continue
        entities.append(SureHubCurfewSwitch(account, device.id))
        for tag in device.tags:
            if tag.id is None:
                continue
            entities.append(
                SureHubIndoorOnlySwitch(
                    account, device.id, tag.id, pet_name.get(tag.id, str(tag.id))
                )
            )
    async_add_entities(entities)


class SureHubCurfewSwitch(SureHubDeviceEntity, SwitchEntity):
    """Enable/disable the flap's curfew (window 0)."""

    def __init__(self, coordinator: SurePetCoordinator, device_id: int) -> None:
        super().__init__(
            coordinator,
            device_id,
            SwitchEntityDescription(key="curfew_enabled", translation_key="curfew_enabled"),
        )

    @property
    def is_on(self) -> bool:
        device = self.device
        window = device.curfew_window if device else None
        return bool(window and window.enabled)

    async def _set_enabled(self, enabled: bool) -> None:
        device = self.device
        if device is None:
            return
        payload = build_curfew(device.curfew_window, enabled=enabled)
        await self.coordinator.client.set_device_control(self._device_id, {"curfew": payload})
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: object) -> None:
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self._set_enabled(False)


class SureHubIndoorOnlySwitch(SureHubDeviceEntity, SwitchEntity):
    """Per-pet 'indoor only' permission on a flap (profile 3 = on, 2 = off)."""

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        device_id: int,
        tag_id: int,
        pet_name: str,
    ) -> None:
        super().__init__(
            coordinator,
            device_id,
            SwitchEntityDescription(
                key=f"indoor_only_{tag_id}",
                translation_key="pet_indoor_only",
            ),
        )
        self._tag_id = tag_id
        self._attr_translation_placeholders = {"pet": pet_name}

    @property
    def is_on(self) -> bool | None:
        device = self.device
        if device is None:
            return None
        profile = device.tag_profile(self._tag_id)
        if profile is None:
            return None
        return profile == PetProfile.INDOOR_ONLY

    async def _set_profile(self, profile: PetProfile) -> None:
        await self.coordinator.client.set_pet_profile(self._device_id, self._tag_id, int(profile))
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: object) -> None:
        await self._set_profile(PetProfile.INDOOR_ONLY)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self._set_profile(PetProfile.OUTDOOR)
