"""Tests for the SureHub data models."""

from __future__ import annotations

from datetime import datetime

from surehub.enums import LockMode, PetLocation, ProductId
from surehub.models import Account, Device


def test_account_parses(account: Account) -> None:
    assert len(account.devices) == 4
    assert len(account.pets) == 1
    assert account.households[0].name == "Test Home"
    assert account.hub is not None
    assert account.hub.product_id == ProductId.HUB


def test_flap_fields(account: Account) -> None:
    flap = account.device(20002)
    assert flap is not None
    assert flap.product_id == ProductId.CAT_FLAP
    assert flap.is_flap is True
    assert flap.parent_device_id == 20001
    assert flap.status.online is True
    assert flap.status.battery == 5.8
    assert flap.status.battery_percentage == 87  # (5.8-4.5)/1.5*100 ≈ 86.7
    assert flap.status.version is not None
    assert flap.status.version.firmware == "335.422"
    assert flap.status.signal is not None
    assert flap.status.signal.device_rssi == -70
    assert flap.curfew_active is False


def test_hub_has_no_battery(account: Account) -> None:
    hub = account.hub
    assert hub is not None
    assert hub.status.battery is None
    assert hub.status.battery_percentage is None


def test_pet_fields(account: Account) -> None:
    pet = account.pet(30001)
    assert pet is not None
    assert pet.name == "Whiskers"
    assert pet.is_inside is True
    assert pet.position is not None
    assert pet.position.where == PetLocation.INSIDE
    assert isinstance(pet.position.since, datetime)
    assert pet.photo_url is not None
    assert pet.photo_url.endswith("whiskers.jpg")
    assert pet.feeding is not None
    assert pet.feeding.total_change == -12.5
    assert pet.drinking is not None
    assert pet.drinking.total_change == -5.0


def test_unknown_product_id_does_not_raise() -> None:
    device = Device.model_validate({"id": 1, "product_id": 999})
    assert device.product_id == ProductId.UNKNOWN


def test_unknown_enum_value_maps_to_unknown() -> None:
    assert LockMode(99) is LockMode.UNKNOWN
    assert PetLocation(99) is PetLocation.UNKNOWN


def test_can_write_true_for_writable_member() -> None:
    account = Account.model_validate(
        {
            "user": {"id": 1},
            "households": [{"id": 9, "users": [{"write": True, "user": {"id": 1}}]}],
        }
    )
    assert account.can_write is True


def test_can_write_false_for_readonly_member() -> None:
    account = Account.model_validate(
        {
            "user": {"id": 2},
            "households": [{"id": 9, "users": [{"write": False, "user": {"id": 2}}]}],
        }
    )
    assert account.can_write is False
