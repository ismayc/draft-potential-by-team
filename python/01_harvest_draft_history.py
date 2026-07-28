"""Harvest NBA draft history for the two-round era (1989-present).

One nba_api DraftHistory call. Cached: a re-run touches nothing fetched.
The same endpoint feeds ../draft-study; this repo keeps its own copy so the
pipeline is self-contained.

Run: .venv/bin/python python/01_harvest_draft_history.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

FIRST_TWO_ROUND_YEAR = 1989


def patch_nba_api_ua() -> None:
    """stats.nba.com hangs UAs that claim a browser the TLS fingerprint
    can't back up (see basketball-data-science
    docs/findings/nba-data-tooling-gotchas.md)."""
    from nba_api.stats.library import http as nba_http
    nba_http.STATS_HEADERS["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")


def harvest_draft_history() -> None:
    out = DATA / "draft_history.csv"
    if out.exists():
        print(f"already present: {out}")
        return
    _fetch_draft_history(out)  # pragma: no cover — network path


# Network I/O is excluded from unit coverage (pragma): it is exercised by
# the real harvest run and guarded by the row-count/name gates instead.
def _fetch_draft_history(out) -> None:  # pragma: no cover
    from nba_api.stats.endpoints import drafthistory
    df = drafthistory.DraftHistory(timeout=60).get_data_frames()[0]
    df["SEASON"] = df["SEASON"].astype(int)
    df = df[df["SEASON"] >= FIRST_TWO_ROUND_YEAR]
    df = df.sort_values(["SEASON", "OVERALL_PICK"])
    df.to_csv(out, index=False)
    years = df["SEASON"].nunique()
    print(f"wrote {out}: {len(df):,} picks across {years} drafts "
          f"({df['SEASON'].min()}-{df['SEASON'].max()})")


def main() -> int:
    DATA.mkdir(exist_ok=True)
    patch_nba_api_ua()
    harvest_draft_history()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
