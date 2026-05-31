"""Base Pydantic model for SureHub API objects."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SureModel(BaseModel):
    """Base model.

    ``extra="ignore"`` keeps parsing resilient: the API is undocumented and may
    add fields at any time without breaking us.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
