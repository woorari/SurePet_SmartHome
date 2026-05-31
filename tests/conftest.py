"""Shared test fixtures."""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from surehub.models import Account

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def me_start_data() -> dict[str, Any]:
    """Raw /me/start response payload."""
    return json.loads((FIXTURES / "me_start.json").read_text())


@pytest.fixture
def account(me_start_data: dict[str, Any]) -> Account:
    """Parsed account graph."""
    return Account.model_validate(me_start_data["data"])
