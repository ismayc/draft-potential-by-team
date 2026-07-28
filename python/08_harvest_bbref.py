"""Harvest career value metrics per draft pick from Basketball-Reference.

One page per draft year (basketball-reference.com/draft/NBA_{year}.html)
carries career Win Shares, WS/48, BPM, and VORP for every pick — the value
measures career minutes cannot see. robots.txt sets Crawl-Delay: 3 for
User-agent: * and does not disallow /draft/; this script identifies itself,
sleeps 4s, and caches raw HTML in data/raw/bbref/ so each page is fetched
at most once, ever.

Rows are joined to data/draft_history.csv by (year, normalised player
name), NOT by pick number: the two sources number some drafts differently
around forfeited picks (e.g. the voided 2001 Minnesota first-rounder), and
draft_history's numbering is canonical everywhere else in this repo. Gate:
every draft_history pick must match exactly one bbref row; anything
unmatched or ambiguous fails the run.

Reads  data/draft_history.csv, data/manual/aliases.csv
Writes data/raw/bbref/{year}.html, data/bbref_draft.csv

Run: .venv/bin/python python/08_harvest_bbref.py
"""
from __future__ import annotations

import csv
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from draftlib import norm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw" / "bbref"
ALIASES = DATA / "manual" / "aliases.csv"

FIRST_YEAR = 1989
LAST_YEAR = 2025
UA = ("draft-potential-by-team harvest "
      "(personal research; contact chester.ismay@gmail.com)")
URL = "https://www.basketball-reference.com/draft/NBA_{year}.html"

STATS = ["ws", "ws_per_48", "bpm", "vorp", "g", "mp", "seasons"]
FIELDS = ["year", "pick", "player"] + STATS


def fetch_all() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        out = RAW / f"{year}.html"
        if out.exists():
            continue
        _fetch(year, out)  # pragma: no cover — network path


# Network I/O is excluded from unit coverage (pragma): it is exercised by
# the real harvest run; every parse is gated afterwards.
def _fetch(year: int, out: Path) -> None:  # pragma: no cover
    req = urllib.request.Request(URL.format(year=year),
                                 headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=60).read()
    out.write_bytes(html)
    print(f"  fetched {year}: {len(html):,} bytes")
    time.sleep(4.0)


def parse_year(year: int) -> list[dict]:
    soup = BeautifulSoup((RAW / f"{year}.html").read_text(), "lxml")
    table = soup.find("table", id="stats")
    assert table is not None, f"{year}: stats table not found"
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = {c.get("data-stat"): c.get_text(strip=True)
                 for c in tr.find_all(["td", "th"])}
        # Round separators and repeated header rows carry no numeric pick.
        if not cells.get("pick_overall", "").isdigit() \
                or not cells.get("player"):
            continue
        rows.append({"year": year,
                     "pick": int(cells["pick_overall"]),
                     "player": cells["player"],
                     **{s: cells.get(s, "") for s in STATS}})
    return rows


def load_aliases() -> dict[str, str]:
    with ALIASES.open() as f:
        return {r["lottery_name"]: r["nba_name"] for r in csv.DictReader(f)}


def main() -> int:
    fetch_all()
    by_year: dict[int, dict[str, list[tuple[int, str]]]] = {}
    with (DATA / "draft_history.csv").open() as f:
        for r in csv.DictReader(f):
            year = int(r["SEASON"])
            by_year.setdefault(year, {}).setdefault(
                norm(r["PLAYER_NAME"]), []).append(
                (int(r["OVERALL_PICK"]), r["PLAYER_NAME"]))
    aliases = load_aliases()

    all_rows: list[dict] = []
    problems: list[str] = []
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        rows = parse_year(year)
        if not 50 <= len(rows) <= 60:
            problems.append(f"{year}: {len(rows)} picks parsed")
        matched: set[int] = set()
        for r in rows:
            n = norm(aliases.get(r["player"], r["player"]))
            hits = by_year[year].get(n, [])
            if len(hits) != 1:
                problems.append(f"{year}: bbref {r['player']!r} matched "
                                f"{len(hits)} draft_history names")
                continue
            pick, nba_name = hits[0]
            matched.add(pick)
            all_rows.append({**r, "pick": pick, "player": nba_name})
        expected = {p for hs in by_year[year].values() for p, _ in hs}
        for p in sorted(expected - matched):
            problems.append(f"{year} pick {p}: no bbref match")

    if problems:
        print("GATE FAILURES:", file=sys.stderr)
        for p in problems[:60]:
            print(f"  {p}", file=sys.stderr)
        return 1

    out = DATA / "bbref_draft.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    print(f"wrote {out}: {len(all_rows):,} picks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
