"""Image entities for Surepet SmartHome (pet photos)."""

from __future__ import annotations

from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from surehub import Pet

from .const import DOMAIN, MANUFACTURER
from .coordinator import SurePetConfigEntry, SurePetCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a photo image entity per pet that has one."""
    account = entry.runtime_data.account
    async_add_entities(
        SureHubPetImage(account, hass, pet.id)
        for pet in account.data.pets
        if pet.photo_url is not None
    )


class SureHubPetImage(CoordinatorEntity[SurePetCoordinator], ImageEntity):
    """A pet's photo, served by Home Assistant for use in notifications/UI."""

    _attr_has_entity_name = True
    entity_description = ImageEntityDescription(key="photo", translation_key="photo")

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        hass: HomeAssistant,
        pet_id: int,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self._pet_id = pet_id
        self._attr_unique_id = f"pet-{pet_id}-photo"

    @property
    def _pet(self) -> Pet | None:
        return self.coordinator.data.pet(self._pet_id)

    @property
    def image_url(self) -> str | None:
        pet = self._pet
        return pet.photo_url if pet else None

    @property
    def device_info(self) -> DeviceInfo:
        pet = self._pet
        return DeviceInfo(
            identifiers={(DOMAIN, f"pet-{self._pet_id}")},
            manufacturer=MANUFACTURER,
            model="Pet",
            name=pet.name if pet else None,
        )

    @property
    def available(self) -> bool:
        return super().available and self._pet is not None
