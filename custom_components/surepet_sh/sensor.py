"""Sensors for Surepet SmartHome."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfMass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from surehub import Device, Pet
from surehub.enums import PetLocation

from .coordinator import SurePetConfigEntry
from .entity import SureHubDeviceEntity, SureHubPetEntity

_LOCATION_OPTIONS = ["inside", "outside"]


@dataclass(frozen=True, kw_only=True)
class SureHubDeviceSensorDescription(SensorEntityDescription):
    """Sensor description for a device."""

    value_fn: Callable[[Device], StateType | datetime]
    exists_fn: Callable[[Device], bool] = lambda _device: True


@dataclass(frozen=True, kw_only=True)
class SureHubPetSensorDescription(SensorEntityDescription):
    """Sensor description for a pet."""

    value_fn: Callable[[Pet], StateType | datetime]
    exists_fn: Callable[[Pet], bool] = lambda _pet: True


def _location(pet: Pet) -> str | None:
    if pet.position is None:
        return None
    if pet.position.where == PetLocation.INSIDE:
        return "inside"
    if pet.position.where == PetLocation.OUTSIDE:
        return "outside"
    return None


DEVICE_SENSORS: tuple[SureHubDeviceSensorDescription, ...] = (
    SureHubDeviceSensorDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.status.battery_percentage,
        exists_fn=lambda device: device.status.battery is not None,
    ),
    SureHubDeviceSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        suggested_display_precision=2,
        value_fn=lambda device: device.status.battery,
        exists_fn=lambda device: device.status.battery is not None,
    ),
    SureHubDeviceSensorDescription(
        key="signal_strength",
        translation_key="signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.status.signal.device_rssi if device.status.signal else None,
        exists_fn=lambda device: (
            device.status.signal is not None and device.status.signal.device_rssi is not None
        ),
    ),
)

PET_SENSORS: tuple[SureHubPetSensorDescription, ...] = (
    SureHubPetSensorDescription(
        key="location",
        translation_key="location",
        device_class=SensorDeviceClass.ENUM,
        options=_LOCATION_OPTIONS,
        value_fn=_location,
    ),
    SureHubPetSensorDescription(
        key="location_since",
        translation_key="location_since",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda pet: pet.position.since if pet.position else None,
        exists_fn=lambda pet: pet.position is not None,
    ),
    SureHubPetSensorDescription(
        key="last_feeding",
        translation_key="last_feeding",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda pet: pet.feeding.at if pet.feeding else None,
        exists_fn=lambda pet: pet.feeding is not None,
    ),
    SureHubPetSensorDescription(
        key="last_feeding_change",
        translation_key="last_feeding_change",
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda pet: pet.feeding.total_change if pet.feeding else None,
        exists_fn=lambda pet: pet.feeding is not None,
    ),
    SureHubPetSensorDescription(
        key="last_drinking",
        translation_key="last_drinking",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda pet: pet.drinking.at if pet.drinking else None,
        exists_fn=lambda pet: pet.drinking is not None,
    ),
    SureHubPetSensorDescription(
        key="last_drinking_change",
        translation_key="last_drinking_change",
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda pet: pet.drinking.total_change if pet.drinking else None,
        exists_fn=lambda pet: pet.drinking is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for device in coordinator.data.devices:
        entities.extend(
            SureHubDeviceSensor(coordinator, device.id, desc)
            for desc in DEVICE_SENSORS
            if desc.exists_fn(device)
        )
    for pet in coordinator.data.pets:
        entities.extend(
            SureHubPetSensor(coordinator, pet.id, desc)
            for desc in PET_SENSORS
            if desc.exists_fn(pet)
        )
    async_add_entities(entities)


class SureHubDeviceSensor(SureHubDeviceEntity, SensorEntity):
    """A device sensor."""

    entity_description: SureHubDeviceSensorDescription

    @property
    def native_value(self) -> StateType | datetime:
        device = self.device
        return self.entity_description.value_fn(device) if device else None


class SureHubPetSensor(SureHubPetEntity, SensorEntity):
    """A pet sensor."""

    entity_description: SureHubPetSensorDescription

    @property
    def native_value(self) -> StateType | datetime:
        pet = self.pet
        return self.entity_description.value_fn(pet) if pet else None
