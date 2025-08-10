from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from .apple_music import AppleMusicClient, AppleMusicConfig
from .models import Track
from .scraper import fetch_tracks_from_feed
from .state import SeenState


app = typer.Typer(help="Stereogum → Apple Music automator")


def get_state() -> SeenState:
    data_dir = Path(os.getenv("STEREOGUM_DATA_DIR", ".stereogum_data"))
    return SeenState(data_dir / "seen.json")


def load_cfg() -> Optional[AppleMusicConfig]:
    return AppleMusicConfig.from_env()


def resolve_feed_url(feed_url: Optional[str]) -> str:
    return feed_url or os.getenv(
        "STEREOGUM_FEED_URL", "https://www.stereogum.com/category/music/feed/"
    )


@app.command()
def scrape(limit: int = typer.Option(30, help="Max posts to consider"), feed_url: Optional[str] = None):
    """Print a deduped list of Artist — Song from the Stereogum feed."""
    load_dotenv()
    tracks = fetch_tracks_from_feed(resolve_feed_url(feed_url), limit=limit)
    state = get_state()
    state.load()
    new = [t for t in tracks if not state.has(t.key())]
    if not new:
        typer.echo("No new tracks found.")
        raise typer.Exit(0)
    for t in new:
        typer.echo(f"• {t.artist} — {t.title}")


@app.command()
def sync(
    playlist: str = typer.Option(
        os.getenv("PLAYLIST_NAME", "Stereogum New Music"),
        help="Target Apple Music playlist name",
    ),
    limit: int = typer.Option(30, help="Max posts to consider"),
    feed_url: Optional[str] = None,
):
    """Sync latest Stereogum tracks into an Apple Music playlist."""
    load_dotenv()
    cfg = load_cfg()
    tracks = fetch_tracks_from_feed(resolve_feed_url(feed_url), limit=limit)
    state = get_state(); state.load()
    new = [t for t in tracks if not state.has(t.key())]

    if not new:
        typer.echo("No new tracks to sync.")
        raise typer.Exit(0)

    if not cfg:
        typer.echo("Apple Music credentials not set; printing dry-run instead.\n")
        for t in new:
            typer.echo(f"• {t.artist} — {t.title}")
        raise typer.Exit(1)

    client = AppleMusicClient(cfg)
    pl_id = client.ensure_playlist(playlist, description="Auto-added from Stereogum")

    # Search and collect catalog IDs
    catalog_ids: list[str] = []
    for t in new:
        q = t.query()
        try:
            res = client.search_song(q)
        except Exception as e:
            typer.echo(f"Search failed for {q}: {e}")
            continue
        if not res:
            typer.echo(f"No match: {q}")
            continue
        catalog_ids.append(res["id"])  # catalog song id
        typer.echo(f"Match: {t.artist} — {t.title} → {res['attributes'].get('name')} by {res['attributes'].get('artistName')}")

    if not catalog_ids:
        typer.echo("No matched songs; nothing to add.")
        raise typer.Exit(0)

    # Add to library first, then fetch library IDs and add to playlist
    client.add_catalog_songs_to_library(catalog_ids)
    lib_ids = client.catalog_to_library_ids(catalog_ids)
    client.add_to_playlist(pl_id, lib_ids)

    # Mark seen and persist
    for t in new:
        state.add(t.key())
    state.save()
    typer.echo(f"Added {len(lib_ids)} songs to playlist '{playlist}'.")


if __name__ == "__main__":
    app()

