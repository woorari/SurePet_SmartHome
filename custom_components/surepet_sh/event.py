"""Event entities for Surepet SmartHome.

Modern automation triggers: each fires when the coordinator observes a change.
"""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from surehub.enums import PetLocation

from .coordinator import SurePetConfigEntry, SurePetCoordinator
from .entity import SureHubPetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SurePetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up pet event entities."""
    account = entry.runtime_data.account
    entities: list[EventEntity] = []
    for pet in account.data.pets:
        entities.append(SureHubMovementEvent(account, pet.id))
        entities.append(SureHubFeedingEvent(account, pet.id))
        entities.append(SureHubDrinkingEvent(account, pet.id))
    async_add_entities(entities)


class SureHubMovementEvent(SureHubPetEntity, EventEntity):
    """Fires when a pet moves through a flap."""

    _attr_event_types = ["entered", "left"]

    def __init__(self, coordinator: SurePetCoordinator, pet_id: int) -> None:
        super().__init__(
            coordinator,
            pet_id,
            EventEntityDescription(key="movement", translation_key="movement"),
        )
        self._last_where: PetLocation | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        pet = self.pet
        if pet is not None and pet.position is not None:
            where = pet.position.where
            if self._last_where is not None and where != self._last_where:
                if where == PetLocation.INSIDE:
                    self._trigger_event("entered")
                elif where == PetLocation.OUTSIDE:
                    self._trigger_event("left")
            self._last_where = where
        super()._handle_coordinator_update()


class SureHubFeedingEvent(SureHubPetEntity, EventEntity):
    """Fires when a pet eats."""

    _attr_event_types = ["fed"]

    def __init__(self, coordinator: SurePetCoordinator, pet_id: int) -> None:
        super().__init__(
            coordinator,
            pet_id,
            EventEntityDescription(key="feeding", translation_key="feeding"),
        )
        self._last_at: datetime | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        pet = self.pet
        if pet is not None and pet.feeding is not None and pet.feeding.at is not None:
            at = pet.feeding.at
            if self._last_at is not None and at != self._last_at:
                self._trigger_event("fed", {"grams": pet.feeding.total_change})
            self._last_at = at
        super()._handle_coordinator_update()


class SureHubDrinkingEvent(SureHubPetEntity, EventEntity):
    """Fires when a pet drinks."""

    _attr_event_types = ["drank"]

    def __init__(self, coordinator: SurePetCoordinator, pet_id: int) -> None:
        super().__init__(
            coordinator,
            pet_id,
            EventEntityDescription(key="drinking", translation_key="drinking"),
        )
        self._last_at: datetime | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        pet = self.pet
        if pet is not None and pet.drinking is not None and pet.drinking.at is not None:
            at = pet.drinking.at
            if self._last_at is not None and at != self._last_at:
                self._trigger_event("drank", {"grams": pet.drinking.total_change})
            self._last_at = at
        super()._handle_coordinator_update()
