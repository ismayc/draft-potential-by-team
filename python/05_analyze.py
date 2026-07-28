"""Analyze the two questions the data was harvested for:

  1. Which colleges produce the best NBA talent?
  2. Which teams have drafted the best players?

"Best" is measured in career regular-season minutes — the least glamorous
and most honest cumulative measure this dataset supports: teams give minutes
to players who help them win, and minutes accrue across roles in a way
points do not. Value is measured against the draft slot: a pick's expected
career minutes is the mean over its pick bucket, so a team (or college) is
credited only for outperforming where the player was taken.

Window: draft classes 1989-2015, so every player has had 10 NBA seasons to
accumulate a career. Later classes are still writing theirs.

Mirrored line for line by R/05_analyze.R; python/06_reconcile.py fails the
build if the two disagree.

Reads  data/draft_history.csv, data/career_totals.csv
Writes output/pick_curve.csv, output/colleges.csv, output/teams.csv,
       output/steals.csv

Run: .venv/bin/python python/05_analyze.py
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

WINDOW = (1989, 2015)      # classes with 10+ seasons of accumulation
HIT_MINUTES = 10_000       # a solid multi-year rotation career
MIN_DRAFTEES = 8           # college table entry floor

# Pick buckets: singles are too noisy (one Ginobili moves pick 57's mean
# more than every other pick-57 combined); eras are compared on ranges.
BUCKETS = [(1, 5), (6, 10), (11, 14), (15, 20), (21, 30), (31, 45), (46, 60)]


def bucket_of(pick: int) -> str:
    for lo, hi in BUCKETS:
        if lo <= pick <= hi:
            return f"{lo}-{hi}"
    return f"{BUCKETS[-1][0]}-{BUCKETS[-1][1]}"


def load() -> list[dict]:
    minutes: dict[int, float] = {}
    with (DATA / "career_totals.csv").open() as f:
        for r in csv.DictReader(f):
            minutes[int(float(r["PLAYER_ID"]))] = float(r["MIN"] or 0)
    rows = []
    with (DATA / "draft_history.csv").open() as f:
        for r in csv.DictReader(f):
            rows.append({
                "year": int(r["SEASON"]),
                "pick": int(r["OVERALL_PICK"]),
                "player": r["PLAYER_NAME"],
                "team_id": int(r["TEAM_ID"]),
                "team": f"{r['TEAM_CITY']} {r['TEAM_NAME']}".strip(),
                "org": r["ORGANIZATION"],
                "org_type": r["ORGANIZATION_TYPE"],
                "min": minutes.get(int(r["PERSON_ID"]), 0.0),
            })
    return rows


def main() -> int:
    OUT.mkdir(exist_ok=True)
    rows = load()

    # Current franchise label: city + name on the id's most recent pick.
    label: dict[int, str] = {}
    for r in sorted(rows, key=lambda r: (r["year"], r["pick"])):
        label[r["team_id"]] = r["team"]

    window = [r for r in rows if WINDOW[0] <= r["year"] <= WINDOW[1]]

    # ── Pick-value curve: mean career minutes by pick bucket ──────────────
    by_bucket: dict[str, list[float]] = defaultdict(list)
    for r in window:
        by_bucket[bucket_of(r["pick"])].append(r["min"])
    curve = {b: sum(v) / len(v) for b, v in by_bucket.items()}
    with (OUT / "pick_curve.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "picks", "mean_min"])
        for lo, hi in BUCKETS:
            b = f"{lo}-{hi}"
            w.writerow([b, len(by_bucket[b]), round(curve[b], 1)])

    for r in window:
        r["expected"] = curve[bucket_of(r["pick"])]
        r["value"] = r["min"] - r["expected"]

    # ── Colleges ──────────────────────────────────────────────────────────
    colleges: dict[str, list[dict]] = defaultdict(list)
    for r in window:
        if r["org_type"] == "College/University":
            colleges[r["org"]].append(r)
    with (OUT / "colleges.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["college", "draftees", "hits", "hit_rate",
                    "total_min", "value_added"])
        table = []
        for org, picks in colleges.items():
            if len(picks) < MIN_DRAFTEES:
                continue
            hits = sum(1 for p in picks if p["min"] >= HIT_MINUTES)
            table.append([
                org, len(picks), hits, round(hits / len(picks), 3),
                round(sum(p["min"] for p in picks), 1),
                round(sum(p["value"] for p in picks), 1)])
        table.sort(key=lambda t: (-t[5], t[0]))
        w.writerows(table)

    # ── Teams ─────────────────────────────────────────────────────────────
    teams: dict[int, list[dict]] = defaultdict(list)
    for r in window:
        teams[r["team_id"]].append(r)
    with (OUT / "teams.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["team", "picks", "avg_pick", "hits",
                    "total_min", "expected_min", "value_added"])
        table = []
        for tid, picks in teams.items():
            hits = sum(1 for p in picks if p["min"] >= HIT_MINUTES)
            table.append([
                label[tid], len(picks),
                round(sum(p["pick"] for p in picks) / len(picks), 1), hits,
                round(sum(p["min"] for p in picks), 1),
                round(sum(p["expected"] for p in picks), 1),
                round(sum(p["value"] for p in picks), 1)])
        table.sort(key=lambda t: (-t[6], t[0]))
        w.writerows(table)

    # ── Steals: the biggest single-pick over-performances ─────────────────
    steals = sorted(window, key=lambda r: (-r["value"], r["player"]))[:15]
    with (OUT / "steals.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["player", "year", "pick", "team", "college",
                    "career_min", "expected_min", "value_added"])
        for r in steals:
            w.writerow([r["player"], r["year"], r["pick"], label[r["team_id"]],
                        r["org"], round(r["min"], 1),
                        round(r["expected"], 1), round(r["value"], 1)])

    print(f"window {WINDOW[0]}-{WINDOW[1]}: {len(window)} picks, "
          f"{len([t for t in teams])} franchises")
    for name in ("pick_curve", "colleges", "teams", "steals"):
        print(f"wrote output/{name}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
