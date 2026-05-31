"""Base entities for Surepet SmartHome."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from surehub import Device, Pet

from .const import DOMAIN, MANUFACTURER
from .coordinator import SurePetCoordinator


class SureHubDeviceEntity(CoordinatorEntity[SurePetCoordinator]):
    """Base entity bound to a Sure Petcare device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        device_id: int,
        description,  # noqa: ANN001 - platform-specific EntityDescription
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"{device_id}-{description.key}"

    @property
    def device(self) -> Device | None:
        return self.coordinator.data.device(self._device_id)

    @property
    def device_info(self) -> DeviceInfo:
        info = DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            manufacturer=MANUFACTURER,
        )
        device = self.device
        if device is not None:
            info["name"] = device.name
            info["model"] = device.product_name
            if device.serial_number:
                info["serial_number"] = device.serial_number
            if device.status.version and device.status.version.firmware:
                info["sw_version"] = device.status.version.firmware
            if device.parent_device_id:
                info["via_device"] = (DOMAIN, str(device.parent_device_id))
        return info

    @property
    def available(self) -> bool:
        return super().available and self.device is not None


class SureHubPetEntity(CoordinatorEntity[SurePetCoordinator]):
    """Base entity bound to a pet."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SurePetCoordinator,
        pet_id: int,
        description,  # noqa: ANN001 - platform-specific EntityDescription
    ) -> None:
        super().__init__(coordinator)
        self._pet_id = pet_id
        self.entity_description = description
        self._attr_unique_id = f"pet-{pet_id}-{description.key}"

    @property
    def pet(self) -> Pet | None:
        return self.coordinator.data.pet(self._pet_id)

    @property
    def device_info(self) -> DeviceInfo:
        pet = self.pet
        return DeviceInfo(
            identifiers={(DOMAIN, f"pet-{self._pet_id}")},
            manufacturer=MANUFACTURER,
            model="Pet",
            name=pet.name if pet else None,
        )

    @property
    def entity_picture(self) -> str | None:
        pet = self.pet
        return pet.photo_url if pet else None

    @property
    def available(self) -> bool:
        return super().available and self.pet is not None
