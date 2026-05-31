"""SureHub — async client for the Sure Petcare (SureHub) cloud API."""

from __future__ import annotations

import logging

from .client import SureHubClient
from .command import Command
from .enums import (
    BowlType,
    FoodType,
    HubLedMode,
    LockMode,
    PetLocation,
    PetProfile,
    ProductId,
)
from .exceptions import ApiError, AuthError, AuthExpiredError, SureHubError
from .models import Account, Device, Household, Pet

__version__ = "0.1.0"

# Never let tokens/credentials reach logs by accident.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "Account",
    "ApiError",
    "AuthError",
    "AuthExpiredError",
    "BowlType",
    "Command",
    "Device",
    "FoodType",
    "Household",
    "HubLedMode",
    "LockMode",
    "Pet",
    "PetLocation",
    "PetProfile",
    "ProductId",
    "SureHubClient",
    "SureHubError",
    "__version__",
]
