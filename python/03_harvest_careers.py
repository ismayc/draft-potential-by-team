"""Harvest NBA career stats for every player drafted 1989-present.

nba_api PlayerCareerStats, one call per PERSON_ID in data/draft_history.csv
(~2,155 players, ~0.6s sleep per call: roughly an hour end to end). Each
player's frames are cached to data/cache/careers/{person_id}.csv on first
fetch, so the run is resumable — timeouts are caught, reported, and filled by
simply re-running. The merged outputs are only written once every player is
cached:

  data/careers.csv        one row per player-season-team (TOT rows kept,
                          flagged by TEAM_ABBREVIATION == "TOT")
  data/career_totals.csv  one row per player (CareerTotalsRegularSeason)

Players drafted but never appearing in an NBA game return empty frames; they
are cached as header-only files and appear in neither output.

Run: .venv/bin/python python/03_harvest_careers.py
"""
from __future__ import annotations

import csv
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / "cache" / "careers"

SEASON_COLS = [
    "PLAYER_ID", "SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "PLAYER_AGE",
    "GP", "GS", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT",
    "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK",
    "TOV", "PF", "PTS",
]
TOTAL_COLS = [c for c in SEASON_COLS if c not in
              ("SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "PLAYER_AGE")]


def patch_nba_api_ua() -> None:
    """stats.nba.com hangs UAs that claim a browser the TLS fingerprint
    can't back up (see basketball-data-science
    docs/findings/nba-data-tooling-gotchas.md)."""
    from nba_api.stats.library import http as nba_http
    nba_http.STATS_HEADERS["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")


def _no_data(pid: int) -> bool:
    """True when NBA Stats answers playercareerstats with an empty body."""
    import requests
    from nba_api.stats.library import http as nba_http
    try:
        r = requests.get(
            "https://stats.nba.com/stats/playercareerstats",
            params={"PlayerID": pid, "PerMode": "Totals", "LeagueID": ""},
            headers=dict(nba_http.STATS_HEADERS), timeout=60)
    except requests.RequestException:
        return False
    return r.status_code == 200 and r.text.strip() in ("{}", "")


def person_ids() -> list[int]:
    with (DATA / "draft_history.csv").open() as f:
        return [int(r["PERSON_ID"]) for r in csv.DictReader(f)]


def fetch_missing(ids: list[int]) -> int:
    from nba_api.stats.endpoints import playercareerstats
    missing = [i for i in ids if not (CACHE / f"{i}.csv").exists()]
    print(f"{len(ids):,} players, {len(missing):,} to fetch")
    failures = 0
    for n, pid in enumerate(missing, 1):
        try:
            ep = playercareerstats.PlayerCareerStats(
                player_id=pid, timeout=60)
            season_df, totals_df = ep.get_data_frames()[0:2]
        except Exception as e:
            # The endpoint returns a literal {} for drafted players NBA
            # Stats has no career page for (never signed, or pre-1996
            # careers too marginal to backfill). That is a permanent
            # no-data answer, not a transient failure: cache it as a
            # header-only file so the pipeline can complete. Anything
            # else (timeout, 5xx) stays uncached for the next re-run.
            if _no_data(pid):
                (CACHE / f"{pid}.csv").write_text(",".join(SEASON_COLS) + "\n")
                print(f"  no data on NBA Stats: {pid} (cached as never-played)")
            else:
                failures += 1
                print(f"  FAIL {pid}: {type(e).__name__}: {e}")
                time.sleep(2.0)
            continue
        season_df = season_df.reindex(columns=SEASON_COLS)
        # Season rows and the career-totals row share one cache file,
        # distinguished by SEASON_ID == "CAREER".
        totals_df = totals_df.reindex(columns=TOTAL_COLS)
        with (CACHE / f"{pid}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(SEASON_COLS)
            for r in season_df.itertuples(index=False):
                w.writerow(r)
            for r in totals_df.itertuples(index=False):
                w.writerow([r.PLAYER_ID, "CAREER", "", "", ""] +
                           [getattr(r, c) for c in TOTAL_COLS[1:]])
        if n % 50 == 0:
            print(f"  {n}/{len(missing)} fetched")
        time.sleep(0.6)
    return failures


def merge(ids: list[int]) -> None:
    seasons_out = DATA / "careers.csv"
    totals_out = DATA / "career_totals.csv"
    season_rows: list[list[str]] = []
    total_rows: list[list[str]] = []
    for pid in sorted(set(ids)):
        with (CACHE / f"{pid}.csv").open() as f:
            for r in csv.DictReader(f):
                if r["SEASON_ID"] == "CAREER":
                    total_rows.append([r[c] for c in TOTAL_COLS])
                else:
                    season_rows.append([r[c] for c in SEASON_COLS])
    with seasons_out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(SEASON_COLS)
        w.writerows(season_rows)
    with totals_out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(TOTAL_COLS)
        w.writerows(total_rows)
    print(f"wrote {seasons_out}: {len(season_rows):,} player-season-team rows")
    print(f"wrote {totals_out}: {len(total_rows):,} players with NBA minutes")


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    patch_nba_api_ua()
    ids = person_ids()
    failures = fetch_missing(ids)
    still_missing = [i for i in ids if not (CACHE / f"{i}.csv").exists()]
    if still_missing:
        print(f"{len(still_missing):,} players still uncached "
              f"({failures} failures this run) — re-run to resume")
        return 1
    merge(ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
