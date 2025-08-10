# Stereogum Script

Stereogum → Apple Music Playlist Automator

What it does
- Scrapes Stereogum’s new music feed to extract Artist + Song.
- Searches Apple Music and adds matches to a chosen playlist.
- Keeps a local `seen.json` to avoid duplicates across runs.

Quick start
1) Install Python 3.10+.
2) Create a virtualenv and install deps:
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install -e .`
3) Copy `.env.example` to `.env` and fill in Apple Music credentials (optional for dry-run).
4) Run:
   - `stereogum sync --playlist "Stereogum New Music"` (with credentials)
   - or `stereogum scrape` (dry-run list, no Apple Music calls)

Apple Music credentials (required for playlist sync)
- Apple Developer account needed to generate a Developer Token (ES256 JWT).
- Required env vars (see `.env.example`):
  - `APPLE_MUSIC_TEAM_ID`, `APPLE_MUSIC_KEY_ID`, `APPLE_MUSIC_PRIVATE_KEY_PATH`
  - `APPLE_MUSIC_STOREFRONT` (e.g., `us`)
  - `APPLE_MUSIC_USER_TOKEN` (Music User Token for your Apple ID)

Scheduling
- Local cron: run the `stereogum sync` command daily.
- GitHub Actions: possible with repo secrets, but user tokens are sensitive; prefer local.

Notes
- If credentials are not set, the CLI will default to dry-run output only.
