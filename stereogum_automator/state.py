from __future__ import annotations

import json
from pathlib import Path
from typing import Set


class SeenState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._seen: Set[str] = set()
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self._seen = set(data or [])
            except Exception:
                self._seen = set()
        self._loaded = True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(sorted(self._seen), indent=2))

    def has(self, key: str) -> bool:
        self.load()
        return key in self._seen

    def add(self, key: str) -> None:
        self.load()
        self._seen.add(key)

