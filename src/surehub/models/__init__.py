"""Pydantic models for SureHub API objects."""

from __future__ import annotations

from .account import Account
from .device import (
    Device,
    DeviceControl,
    DeviceStatus,
    DeviceTag,
    FirmwareInfo,
    LockingStatus,
    Signal,
)
from .household import Household, HouseholdUser, Timezone
from .pet import ConsumptionEvent, Pet, Photo, Position
from .report import BowlWeight, PetReport, ReportEvent

__all__ = [
    "Account",
    "BowlWeight",
    "ConsumptionEvent",
    "Device",
    "DeviceControl",
    "DeviceStatus",
    "DeviceTag",
    "FirmwareInfo",
    "Household",
    "HouseholdUser",
    "LockingStatus",
    "Pet",
    "PetReport",
    "Photo",
    "Position",
    "ReportEvent",
    "Signal",
    "Timezone",
]
