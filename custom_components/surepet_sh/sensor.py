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
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from surehub import Device, Pet, PetReport
from surehub.enums import PetLocation

from .coordinator import SurePetConfigEntry
from .entity import SureHubDeviceEntity, SureHubPetEntity, SureHubPetReportEntity

_LOCATION_OPTIONS = ["inside", "outside"]


@dataclass(frozen=True, kw_only=True)
class SureHubDeviceSensorDescription(SensorEntityDescription):
    """Sensor description for a device."""

    value_fn: Callable[[Device], StateType | datetime]
    exists_fn: Callable[[Device], bool] = lambda _device: True


@dataclass(frozen=True, kw_only=True)
class SureHubPetSensorDescription(SensorEntityDescription):
    """Sensor description for a pet (from the account graph)."""

    value_fn: Callable[[Pet], StateType | datetime]
    exists_fn: Callable[[Pet], bool] = lambda _pet: True


@dataclass(frozen=True, kw_only=True)
class SureHubReportSensorDescription(SensorEntityDescription):
    """Sensor description for a pet daily total (from the report)."""

    value_fn: Callable[[PetReport, datetime], StateType]


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
        # Water is measured by weight on the device, but reported as volume
        # (≈1 g/ml) so it reads naturally for a drinking station.
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda pet: pet.drinking.total_change if pet.drinking else None,
        exists_fn=lambda pet: pet.drinking is not None,
    ),
)

REPORT_SENSORS: tuple[SureHubReportSensorDescription, ...] = (
    SureHubReportSensorDescription(
        key="time_outside_today",
        translation_key="time_outside_today",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda report, since: report.time_outside(since),
    ),
    SureHubReportSensorDescription(
        key="trips_today",
        translation_key="trips_today",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda report, since: report.trips(since),
    ),
    SureHubReportSensorDescription(
        key="meals_today",
        translation_key="meals_today",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda report, since: report.meals(since),
    ),
    SureHubReportSensorDescription(
        key="food_eaten_today",
        translation_key="food_eaten_today",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda report, since: report.food_eaten(since),
    ),
    SureHubReportSensorDescription(
        key="drinks_today",
        translation_key="drinks_today",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda report, since: report.drinks(since),
    ),
    SureHubReportSensorDescription(
        key="water_drunk_today",
        translation_key="water_drunk_today",
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda report, since: report.water_drunk(since),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    account = entry.runtime_data.account
    reports = entry.runtime_data.reports
    entities: list[SensorEntity] = []
    for device in account.data.devices:
        entities.extend(
            SureHubDeviceSensor(account, device.id, desc)
            for desc in DEVICE_SENSORS
            if desc.exists_fn(device)
        )
    for pet in account.data.pets:
        entities.extend(
            SureHubPetSensor(account, pet.id, desc) for desc in PET_SENSORS if desc.exists_fn(pet)
        )
        entities.extend(
            SureHubReportSensor(reports, account, pet.id, desc) for desc in REPORT_SENSORS
        )
    hub = account.data.hub
    if hub is not None:
        entities.append(SureHubNotificationSensor(account, hub.id))
    async_add_entities(entities)


class SureHubDeviceSensor(SureHubDeviceEntity, SensorEntity):
    """A device sensor."""

    entity_description: SureHubDeviceSensorDescription

    @property
    def native_value(self) -> StateType | datetime:
        device = self.device
        return self.entity_description.value_fn(device) if device else None


class SureHubPetSensor(SureHubPetEntity, SensorEntity):
    """A pet sensor (from the account graph)."""

    entity_description: SureHubPetSensorDescription

    @property
    def native_value(self) -> StateType | datetime:
        pet = self.pet
        return self.entity_description.value_fn(pet) if pet else None


class SureHubReportSensor(SureHubPetReportEntity, SensorEntity):
    """A pet daily-total sensor (from the report)."""

    entity_description: SureHubReportSensorDescription

    @property
    def native_value(self) -> StateType:
        report = self.report
        if report is None:
            return None
        return self.entity_description.value_fn(report, dt_util.start_of_local_day())


class SureHubNotificationSensor(SureHubDeviceEntity, SensorEntity):
    """The latest account notification (recent entries in attributes)."""

    def __init__(self, coordinator, device_id: int) -> None:  # noqa: ANN001
        super().__init__(
            coordinator,
            device_id,
            SensorEntityDescription(
                key="latest_notification", translation_key="latest_notification"
            ),
        )

    @property
    def native_value(self) -> StateType:
        notifications = self.coordinator.notifications
        return notifications[0].text[:255] if notifications else None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        notifications = self.coordinator.notifications
        if not notifications:
            return None
        latest = notifications[0]
        return {
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
            "type": latest.type,
            "recent": [note.text for note in notifications[:10]],
        }

    @property
    def last_reset(self) -> datetime:
        # Daily totals reset at local midnight; tells HA's statistics the period.
        return dt_util.start_of_local_day()
