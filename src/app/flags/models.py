from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Flag:
    code: str
    weight: int
    message: str


@dataclass(frozen=True)
class FlaggedRecord:
    record: dict[str, Any]
    severity: int
    flags: list[Flag]

    @property
    def flag_codes(self) -> str:
        return "|".join(f.code for f in self.flags)

    @property
    def flag_messages(self) -> str:
        return " || ".join(f"{f.code}: {f.message}" for f in self.flags)
