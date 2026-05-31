"""Enumerations used across the SureHub API.

All enums tolerate unknown values (the API is undocumented and may add members):
an unrecognised value resolves to ``UNKNOWN`` rather than raising.
"""

from __future__ import annotations

from enum import IntEnum


class _SureIntEnum(IntEnum):
    """IntEnum that maps unknown values to ``UNKNOWN`` instead of raising."""

    @classmethod
    def _missing_(cls, value: object) -> _SureIntEnum:
        return cls.UNKNOWN  # type: ignore[attr-defined,no-any-return]


class ProductId(_SureIntEnum):
    """Device product types."""

    UNKNOWN = -1
    HUB = 1
    REPEATER = 2
    PET_FLAP = 3
    FEEDER = 4
    PROGRAMMER = 5
    CAT_FLAP = 6
    FEEDER_LITE = 7
    FELAQUA = 8


class LockMode(_SureIntEnum):
    """Flap lock modes (``control.locking`` / ``status.locking.mode``)."""

    UNKNOWN = -1
    UNLOCKED = 0
    LOCKED_IN = 1
    LOCKED_OUT = 2
    LOCKED_ALL = 3
    CURFEW = 4


class PetLocation(_SureIntEnum):
    """Where a pet currently is (``position.where``)."""

    UNKNOWN = -1
    INSIDE = 1
    OUTSIDE = 2


class PetProfile(_SureIntEnum):
    """Per-pet permission on a flap (``tag.profile``)."""

    UNKNOWN = -1
    OUTDOOR = 2  # pet is allowed outside
    INDOOR_ONLY = 3  # pet is restricted indoors


class FoodType(_SureIntEnum):
    """Feeder bowl food type."""

    UNKNOWN = -1
    WET = 1
    DRY = 2


class BowlType(_SureIntEnum):
    """Feeder bowl configuration."""

    UNKNOWN = -1
    SINGLE = 1
    HALF = 4


class HubLedMode(_SureIntEnum):
    """Hub LED brightness."""

    UNKNOWN = -1
    OFF = 0
    HIGH = 1
    DIMMED = 4


PRODUCT_NAMES: dict[ProductId, str] = {
    ProductId.HUB: "Hub",
    ProductId.REPEATER: "Repeater",
    ProductId.PET_FLAP: "Pet Flap Connect",
    ProductId.FEEDER: "Feeder Connect",
    ProductId.PROGRAMMER: "Programmer",
    ProductId.CAT_FLAP: "Cat Flap Connect",
    ProductId.FEEDER_LITE: "Feeder Lite",
    ProductId.FELAQUA: "Felaqua Connect",
    ProductId.UNKNOWN: "Sure Petcare Device",
}
