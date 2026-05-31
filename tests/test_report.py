"""Tests for the per-pet report model and daily-total derivations."""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import pytest

from surehub.models import PetReport

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
# Start of the fixture's "today".
SINCE = datetime(2026, 5, 31, 0, 0, 0, tzinfo=UTC)


@pytest.fixture
def report() -> PetReport:
    data = json.loads((FIXTURES / "report.json").read_text())
    return PetReport.model_validate(data["data"])


def test_parses_datapoints(report: PetReport) -> None:
    assert len(report.movement) == 2
    assert len(report.feeding) == 4
    assert len(report.drinking) == 2


def test_daily_totals(report: PetReport) -> None:
    # Only today's datapoints count; refills (positive change) are not meals.
    assert report.time_outside(SINCE) == 3600
    assert report.trips(SINCE) == 1
    assert report.meals(SINCE) == 2
    assert report.food_eaten(SINCE) == 30
    assert report.drinks(SINCE) == 1
    assert report.water_drunk(SINCE) == 5


def test_consumed_ignores_refills(report: PetReport) -> None:
    refill = report.feeding[1]  # context 5, change +100
    assert refill.consumed == 0.0
