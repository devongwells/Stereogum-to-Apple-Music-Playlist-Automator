from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx
import jwt


@dataclass
class AppleMusicConfig:
    team_id: str
    key_id: str
    private_key_path: Path
    storefront: str = "us"
    user_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> Optional["AppleMusicConfig"]:
        import os

        team_id = os.getenv("APPLE_MUSIC_TEAM_ID")
        key_id = os.getenv("APPLE_MUSIC_KEY_ID")
        pk_path = os.getenv("APPLE_MUSIC_PRIVATE_KEY_PATH")
        storefront = os.getenv("APPLE_MUSIC_STOREFRONT", "us")
        user_token = os.getenv("APPLE_MUSIC_USER_TOKEN")

        if not (team_id and key_id and pk_path):
            return None
        return cls(
            team_id=team_id,
            key_id=key_id,
            private_key_path=Path(pk_path),
            storefront=storefront,
            user_token=user_token,
        )


class AppleMusicClient:
    def __init__(self, cfg: AppleMusicConfig):
        self.cfg = cfg
        self._dev_token = self._generate_dev_token()
        self._client = httpx.Client(base_url="https://api.music.apple.com", timeout=20.0)

    def _generate_dev_token(self) -> str:
        pk = self.cfg.private_key_path.read_text().encode()
        headers = {"alg": "ES256", "kid": self.cfg.key_id, "typ": "JWT"}
        now = int(time.time())
        payload = {
            "iss": self.cfg.team_id,
            "iat": now,
            "exp": now + 60 * 60 * 12,  # 12 hours
        }
        return jwt.encode(payload, pk, algorithm="ES256", headers=headers)

    def _auth_headers(self, user: bool = False) -> Dict[str, str]:
        h = {"Authorization": f"Bearer {self._dev_token}"}
        if user and self.cfg.user_token:
            h["Music-User-Token"] = self.cfg.user_token
        return h

    # Catalog search
    def search_song(self, term: str, limit: int = 5) -> Optional[Dict[str, Any]]:
        r = self._client.get(
            f"/v1/catalog/{self.cfg.storefront}/search",
            params={"term": term, "types": "songs", "limit": str(limit)},
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        data = r.json()
        songs = data.get("results", {}).get("songs", {}).get("data", [])
        return songs[0] if songs else None

    # Library helpers
    def ensure_playlist(self, name: str, description: str = "") -> str:
        # Try to find existing playlist by name
        r = self._client.get(
            "/v1/me/library/playlists",
            headers=self._auth_headers(user=True),
        )
        r.raise_for_status()
        for pl in r.json().get("data", []):
            if pl.get("attributes", {}).get("name") == name:
                return pl["id"]

        # Create new
        body = {
            "attributes": {"name": name, "description": description},
            "relationships": {},
            "type": "library-playlists",
        }
        r2 = self._client.post(
            "/v1/me/library/playlists",
            headers={**self._auth_headers(user=True), "Content-Type": "application/json"},
            content=json.dumps(body),
        )
        r2.raise_for_status()
        return r2.json()["data"][0]["id"]

    def add_catalog_songs_to_library(self, catalog_ids: list[str]) -> None:
        if not catalog_ids:
            return
        r = self._client.post(
            "/v1/me/library",
            headers=self._auth_headers(user=True),
            params={"ids[songs]": ",".join(catalog_ids)},
        )
        r.raise_for_status()

    def catalog_to_library_ids(self, catalog_ids: list[str]) -> list[str]:
        if not catalog_ids:
            return []
        r = self._client.get(
            "/v1/me/library/songs",
            headers=self._auth_headers(user=True),
            params={"filter[catalogIds]": ",".join(catalog_ids), "limit": "100"},
        )
        r.raise_for_status()
        lib = r.json().get("data", [])
        return [s["id"] for s in lib]

    def add_to_playlist(self, playlist_id: str, library_song_ids: list[str]) -> None:
        if not library_song_ids:
            return
        body = {
            "data": [{"id": sid, "type": "library-songs"} for sid in library_song_ids]
        }
        r = self._client.post(
            f"/v1/me/library/playlists/{playlist_id}/tracks",
            headers={**self._auth_headers(user=True), "Content-Type": "application/json"},
            content=json.dumps(body),
        )
        r.raise_for_status()

