"""Switch entities for Surepet SmartHome (write/control)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.storage import Store

from surehub.enums import LockMode, PetProfile

from .const import DOMAIN, MANUFACTURER
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
    pet_by_tag = {pet.tag_id: pet for pet in account.data.pets if pet.tag_id is not None}
    entities: list[SwitchEntity] = []
    flaps = [device for device in account.data.devices if device.is_flap]
    for device in flaps:
        entities.append(SureHubCurfewSwitch(account, device.id))
        for tag in device.tags:
            if tag.id is None:
                continue
            pet = pet_by_tag.get(tag.id)
            entities.append(
                SureHubIndoorOnlySwitch(
                    account,
                    device.id,
                    tag.id,
                    device.name,
                    pet_id=pet.id if pet else None,
                )
            )
    # Responsive mode (fast polling) for devices that support it.
    for device in account.data.devices:
        if device.control.fast_polling is not None:
            entities.append(SureHubResponsiveModeSwitch(account, device.id))
    # Household-level emergency unlock, anchored to the hub.
    hub = account.data.hub
    if hub is not None and flaps:
        entities.append(SureHubEmergencyUnlockSwitch(account, hub.id, hass, entry.entry_id))
    async_add_entities(entities)


class SureHubResponsiveModeSwitch(SureHubDeviceEntity, SwitchEntity):
    """Fast-polling 'responsive mode' for a device (higher battery use)."""

    def __init__(self, coordinator: SurePetCoordinator, device_id: int) -> None:
        super().__init__(
            coordinator,
            device_id,
            SwitchEntityDescription(
                key="responsive_mode",
                translation_key="responsive_mode",
                entity_category=EntityCategory.CONFIG,
            ),
        )

    @property
    def is_on(self) -> bool | None:
        device = self.device
        return device.control.fast_polling if device else None

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.client.set_device_control(self._device_id, {"fast_polling": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.client.set_device_control(self._device_id, {"fast_polling": False})
        await self.coordinator.async_request_refresh()


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
    """Per-pet 'indoor only' permission on a flap (profile 3 = on, 2 = off).

    Bound to the flap for state and control, but shown on the assigned pet's
    device so the setting lives with the pet it governs.
    """

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        device_id: int,
        tag_id: int,
        flap_name: str,
        pet_id: int | None = None,
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
        self._pet_id = pet_id
        self._attr_translation_placeholders = {"flap": flap_name}

    @property
    def device_info(self) -> DeviceInfo:
        # Render on the assigned pet's device; fall back to the flap when the
        # tag isn't matched to a known pet.
        if self._pet_id is None:
            return super().device_info
        pet = self.coordinator.data.pet(self._pet_id)
        return DeviceInfo(
            identifiers={(DOMAIN, f"pet-{self._pet_id}")},
            manufacturer=MANUFACTURER,
            model="Pet",
            name=pet.name if pet else None,
        )

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


class SureHubEmergencyUnlockSwitch(SureHubDeviceEntity, SwitchEntity, RestoreEntity):
    """Force-open every flap (lock + curfew + per-pet profile) and restore.

    On: snapshot every flap's lock mode, curfew and each pet's profile (persisted
    so a restart can still restore), then unlock all flaps, disable curfew and
    set every pet to outdoor. Off: restore the snapshot.
    """

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        device_id: int,
        hass: HomeAssistant,
        entry_id: str,
    ) -> None:
        super().__init__(
            coordinator,
            device_id,
            SwitchEntityDescription(key="emergency_unlock", translation_key="emergency_unlock"),
        )
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}_emergency_{entry_id}")
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"

    @property
    def available(self) -> bool:
        # Available whenever the account is loaded (not tied to one flap).
        return self.coordinator.last_update_success

    def _flaps(self):  # noqa: ANN202
        return [d for d in self.coordinator.data.devices if d.is_flap]

    async def async_turn_on(self, **kwargs: object) -> None:
        client = self.coordinator.client
        snapshot: dict[str, Any] = {"flaps": [], "profiles": []}
        for flap in self._flaps():
            snapshot["flaps"].append(
                {
                    "id": flap.id,
                    "locking": flap.control.locking,
                    "curfew": [entry.model_dump() for entry in flap.control.curfew],
                }
            )
            for tag in flap.tags:
                if tag.id is not None and tag.profile is not None:
                    snapshot["profiles"].append(
                        {"device_id": flap.id, "tag_id": tag.id, "profile": tag.profile}
                    )
        await self._store.async_save(snapshot)

        for flap in self._flaps():
            control: dict[str, Any] = {"locking": int(LockMode.UNLOCKED)}
            if flap.control.curfew:
                control["curfew"] = [
                    {"enabled": False, "lock_time": e.lock_time, "unlock_time": e.unlock_time}
                    for e in flap.control.curfew
                ]
            await client.set_device_control(flap.id, control)
            for tag in flap.tags:
                if tag.id is not None:
                    await client.set_pet_profile(flap.id, tag.id, int(PetProfile.OUTDOOR))

        self._attr_is_on = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        client = self.coordinator.client
        snapshot = await self._store.async_load()
        if snapshot:
            for flap in snapshot.get("flaps", []):
                control = {}
                if flap.get("locking") is not None:
                    control["locking"] = flap["locking"]
                if flap.get("curfew"):
                    control["curfew"] = flap["curfew"]
                if control:
                    await client.set_device_control(flap["id"], control)
            for profile in snapshot.get("profiles", []):
                await client.set_pet_profile(
                    profile["device_id"], profile["tag_id"], profile["profile"]
                )
            await self._store.async_remove()

        self._attr_is_on = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
