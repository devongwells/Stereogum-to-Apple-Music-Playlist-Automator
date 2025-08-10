from __future__ import annotations

import re
from typing import Iterable, List

import feedparser

from .models import Track


TITLE_PATTERNS: list[re.Pattern[str]] = [
    # Artist – “Song” or 'Song'
    re.compile(r"^(?P<artist>.+?)\s+[–-]\s+[“\"](?P<title>.+?)[”\"]\s*$"),
    # Artist – Song
    re.compile(r"^(?P<artist>.+?)\s+[–-]\s+(?P<title>[^\-\:]+?)\s*$"),
]

SKIP_KEYWORDS = [
    "the number ones",
    "interview",
    "review",
    "q&a",
    "best tracks",
    "we’ve got a file on",
    "premiere:",
    "album stream",
    "stream:",
]


def should_skip(title: str) -> bool:
    lt = title.lower()
    return any(k in lt for k in SKIP_KEYWORDS)


def parse_title(title: str) -> Track | None:
    if should_skip(title):
        return None
    for pat in TITLE_PATTERNS:
        m = pat.match(title.strip())
        if m:
            artist = cleanup(m.group("artist"))
            song = cleanup(m.group("title"))
            if artist and song:
                return Track(artist=artist, title=song)
    return None


def cleanup(s: str) -> str:
    s = s.strip()
    # Remove trailing descriptors like (ft. X), [Prod.], etc. Keep minimal ones.
    s = re.sub(r"\s*\[(prod\.|prod by|prod\])[^\]]*\]$", "", s, flags=re.I)
    s = re.sub(r"\s*\((prod\.|prod by)[^\)]*\)$", "", s, flags=re.I)
    return s.strip("-–— \t\u00a0")


def fetch_tracks_from_feed(feed_url: str, limit: int = 30) -> List[Track]:
    d = feedparser.parse(feed_url)
    tracks: list[Track] = []
    for entry in d.entries[:limit]:
        title = entry.get("title", "").strip()
        link = entry.get("link")
        tr = parse_title(title)
        if tr:
            tr.url = link
            tracks.append(tr)
    return tracks

