"""Binary sensors for Surepet SmartHome."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from surehub import Device, Pet

from .coordinator import SurePetConfigEntry
from .entity import SureHubDeviceEntity, SureHubPetEntity


@dataclass(frozen=True, kw_only=True)
class SureHubDeviceBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description for a device."""

    value_fn: Callable[[Device], bool | None]
    exists_fn: Callable[[Device], bool] = lambda _device: True


@dataclass(frozen=True, kw_only=True)
class SureHubPetBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description for a pet."""

    value_fn: Callable[[Pet], bool | None]
    exists_fn: Callable[[Pet], bool] = lambda _pet: True


DEVICE_BINARY_SENSORS: tuple[SureHubDeviceBinarySensorDescription, ...] = (
    SureHubDeviceBinarySensorDescription(
        key="connectivity",
        translation_key="connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.status.online,
    ),
    SureHubDeviceBinarySensorDescription(
        key="curfew",
        translation_key="curfew",
        value_fn=lambda device: device.curfew_active,
        exists_fn=lambda device: device.is_flap,
    ),
)

PET_BINARY_SENSORS: tuple[SureHubPetBinarySensorDescription, ...] = (
    SureHubPetBinarySensorDescription(
        key="inside",
        translation_key="inside",
        device_class=BinarySensorDeviceClass.PRESENCE,
        value_fn=lambda pet: pet.is_inside,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = entry.runtime_data.account
    entities: list[BinarySensorEntity] = []
    for device in coordinator.data.devices:
        entities.extend(
            SureHubDeviceBinarySensor(coordinator, device.id, desc)
            for desc in DEVICE_BINARY_SENSORS
            if desc.exists_fn(device)
        )
    for pet in coordinator.data.pets:
        entities.extend(
            SureHubPetBinarySensor(coordinator, pet.id, desc)
            for desc in PET_BINARY_SENSORS
            if desc.exists_fn(pet)
        )
    async_add_entities(entities)


class SureHubDeviceBinarySensor(SureHubDeviceEntity, BinarySensorEntity):
    """A device binary sensor."""

    entity_description: SureHubDeviceBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        device = self.device
        return self.entity_description.value_fn(device) if device else None


class SureHubPetBinarySensor(SureHubPetEntity, BinarySensorEntity):
    """A pet binary sensor."""

    entity_description: SureHubPetBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        pet = self.pet
        return self.entity_description.value_fn(pet) if pet else None
