from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    artist: str
    title: str
    url: Optional[str] = None

    def query(self) -> str:
        return f"{self.artist} {self.title}".strip()

    def key(self) -> str:
        return f"{self.artist.lower()} — {self.title.lower()}"

