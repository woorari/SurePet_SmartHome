"""The Command abstraction.

Every API interaction is modelled as a :class:`Command`. A command either
``parse``-s its response into domain data, or ``chain``-s into follow-up
command(s) that the client runs recursively. This keeps multi-step flows
(list → per-item refresh, write → poll → refresh) declarative.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# A parse callback turns a raw response into domain data.
ParseFn = Callable[[Any], Any]
# A chain callback returns follow-up command(s) to run.
ChainFn = Callable[[Any], "Command | list[Command]"]


@dataclass(slots=True)
class Command:
    """A single API request plus how to handle its response."""

    method: str
    endpoint: str
    params: dict[str, Any] | None = None
    json: dict[str, Any] | None = None
    parse: ParseFn | None = None
    chain: ChainFn | None = None

    def __post_init__(self) -> None:
        if not self.method:
            raise ValueError("Command.method must be set")
        if not self.endpoint:
            raise ValueError("Command.endpoint must be set")
        if self.parse is not None and self.chain is not None:
            raise ValueError("Command cannot set both parse and chain")
