"""Harvest NBA draft lottery odds and results for the two-round era
(1989-present).

Source: thedraftreview.com, which keeps one identically-shaped table per year
(#, Team, Representative, Title, Record, Odds, Chances, Difference, Pick).
robots.txt grants User-agent: * with Crawl-Delay: 5; this script identifies
itself honestly, sleeps 6s between requests, and caches raw HTML in
data/raw/lottery/ so the site is fetched at most once per year-page, ever.

Every parsed year is gated against data/draft_history.csv (nba_api): the
player listed at lottery position N must be that draft's overall pick N.
Mismatches beyond data/manual/aliases.csv fail the run.

Run: .venv/bin/python python/02_harvest_lottery.py
"""
from __future__ import annotations

import csv
import re
import sys
import time
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from draftlib import norm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw" / "lottery"
ALIASES = DATA / "manual" / "aliases.csv"
CORRECTIONS = DATA / "manual" / "corrections.csv"

FIRST_LOTTERY_YEAR = 1989
LAST_YEAR = 2025
UA = ("draft-potential-by-team harvest "
      "(personal research; contact chester.ismay@gmail.com)")
URL = ("https://www.thedraftreview.com/historical-draft-events/"
       "nba-draft-lottery-history/{year}-nba-draft-lottery")

# Lottery teams per year: 9 in 1989, 11 (1990-94), 13 (1995-2003),
# 14 (2004-). Forfeits can shrink a year (e.g. 2000 Minnesota), so these
# are ceilings checked as row-count ranges.
def expected_teams(year: int) -> int:
    if year == 1989:
        return 9
    if year <= 1994:
        return 11
    if year <= 2003:
        return 13
    return 14


FIELDS = ["year", "result_position", "team", "representative", "rep_title",
          "record_w", "record_l", "odds_pct", "chances", "seed_delta",
          "pre_lottery_seed", "player_picked"]


def fetch_all() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for year in range(FIRST_LOTTERY_YEAR, LAST_YEAR + 1):
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
    time.sleep(6.0)


def parse_year(year: int) -> list[dict]:
    soup = BeautifulSoup((RAW / f"{year}.html").read_text(), "lxml")
    for table in soup.find_all("table"):
        headers = [c.get_text(strip=True)
                   for c in table.find_all(["td", "th"])[:24]]
        if "Team" in headers and "Pick" in headers and "Odds" in headers:
            break
    else:
        raise AssertionError(f"{year}: lottery table not found")

    header_cells = ["#", "Team", "Representative", "Title", "Record",
                    "Odds", "Chances", "Difference", "Pick"]
    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        cells = [c for c in cells if c != ""]
        if len(cells) != len(header_cells) or cells[0] in ("#", ""):
            continue
        pos = int(cells[0].rstrip("."))
        rec = re.fullmatch(r"(\d+)-(\d+)", cells[4])
        odds = re.fullmatch(r"([\d.]+)%", cells[5])
        delta_m = re.search(r"([+-]\s*\d+)", cells[7])
        delta = int(delta_m.group(1).replace(" ", "")) if delta_m else 0
        rows.append({
            "year": year,
            "result_position": pos,
            "team": cells[1],
            "representative": cells[2],
            "rep_title": cells[3],
            "record_w": int(rec.group(1)) if rec else "",
            "record_l": int(rec.group(2)) if rec else "",
            "odds_pct": float(odds.group(1)) if odds else "",
            "chances": int(cells[6]) if cells[6].isdigit() else "",
            "seed_delta": delta,
            # "▲ +10" means the team jumped ten spots UP from its
            # inverse-record seed, so the seed sits delta BELOW the result.
            "pre_lottery_seed": pos + delta,
            "player_picked": cells[8],
        })
    return rows


def apply_corrections(rows: list[dict]) -> None:
    """Documented hand-fixes for values the source prints wrong (each line
    in corrections.csv carries the evidence)."""
    if not CORRECTIONS.exists():
        return
    with CORRECTIONS.open() as f:
        for c in csv.DictReader(f):
            for r in rows:
                if (r["year"] == int(c["year"]) and r["team"] == c["team"]):
                    value = c["value"]
                    r[c["field"]] = int(value) if value.isdigit() else value


def load_aliases() -> dict[str, str]:
    if not ALIASES.exists():
        return {}
    with ALIASES.open() as f:
        return {r["lottery_name"]: r["nba_name"] for r in csv.DictReader(f)}


def load_draft_pick_names() -> dict[tuple[int, int], str]:
    names: dict[tuple[int, int], str] = {}
    with (DATA / "draft_history.csv").open() as f:
        for r in csv.DictReader(f):
            if r["OVERALL_PICK"]:
                names[(int(r["SEASON"]), int(r["OVERALL_PICK"]))] = \
                    r["PLAYER_NAME"]
    return names


def gate(year: int, rows: list[dict], picks: dict[tuple[int, int], str],
         aliases: dict[str, str]) -> list[str]:
    problems = []
    n = expected_teams(year)
    if not (n - 1 <= len(rows) <= n):  # forfeits can drop one team
        problems.append(f"{year}: {len(rows)} rows, expected ~{n}")
    positions = [r["result_position"] for r in rows]
    if positions != list(range(1, len(rows) + 1)):
        problems.append(f"{year}: positions not contiguous: {positions}")
    # Tied records share a printed seed (e.g. two 8s in 2020), so seeds are
    # range-checked rather than required to be a strict permutation.
    seeds = sorted(r["pre_lottery_seed"] for r in rows)
    if seeds and not (1 <= seeds[0] and seeds[-1] <= len(rows)):
        problems.append(f"{year}: seeds out of range 1..{len(rows)}: {seeds}")
    odds_total = sum(r["odds_pct"] for r in rows if r["odds_pct"] != "")
    if not 98.0 <= odds_total <= 102.0:
        problems.append(f"{year}: odds sum {odds_total:.1f}")
    for r in rows:
        # 50 (1999 lockout) to 82 games; anything outside is a misprint.
        # 0-0 is real: expansion teams (1995 TOR/VAN, 2004 CHA) entered the
        # lottery having never played.
        games = (r["record_w"] + r["record_l"]) if r["record_w"] != "" else 0
        if games != 0 and not 50 <= games <= 82:
            problems.append(
                f"{year} {r['team']}: impossible record "
                f"{r['record_w']}-{r['record_l']}")
    for r in rows:
        # draft_history only starts at 1989; earlier years pass name gates
        # vacuously and rely on the structural gates above.
        key = (year, r["result_position"])
        if key not in picks:
            continue
        got = aliases.get(r["player_picked"], r["player_picked"])
        if norm(got) != norm(picks[key]):
            problems.append(
                f"{year} pick {r['result_position']}: lottery says "
                f"{r['player_picked']!r}, draft history says {picks[key]!r}")
    return problems


def main() -> int:
    out = DATA / "lottery.csv"
    fetch_all()
    picks = load_draft_pick_names()
    aliases = load_aliases()

    all_rows: list[dict] = []
    problems: list[str] = []
    for year in range(FIRST_LOTTERY_YEAR, LAST_YEAR + 1):
        rows = parse_year(year)
        apply_corrections(rows)
        problems += gate(year, rows, picks, aliases)
        all_rows.extend(rows)

    if problems:
        print("GATE FAILURES:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    years = LAST_YEAR - FIRST_LOTTERY_YEAR + 1
    print(f"wrote {out}: {len(all_rows):,} rows across {years} lotteries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
