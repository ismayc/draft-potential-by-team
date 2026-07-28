"""Analyze the two questions the data was harvested for:

  1. Which colleges produce the best NBA talent?
  2. Which teams have drafted the best players?

v2. The headline metric is career Win Shares (Basketball-Reference) —
an estimate of wins contributed, so peak impact registers, not just
presence. Career minutes, VORP, and a peak measure (best three consecutive
seasons of NBA Efficiency, from the per-season harvest) ride alongside,
and each career is split into minutes played for the drafting franchise
vs elsewhere.

Value is measured against the pick slot: each outcome's expectation over
picks 1..60 is a weighted isotonic (non-increasing) fit of the per-pick
means — no bucket edges, no functional form — computed on the window and
subtracted per pick. Confidence intervals on team totals are normal
approximations (sum ± 1.96·sd·√n). Era fairness: values are also expressed
in within-class standard deviations (value_ws_z).

Window: draft classes 1989-2015, so every player has had 10 NBA seasons.

Mirrored by R/05_analyze.R; python/06_reconcile.py holds the two equal.

Reads  data/draft_history.csv, data/career_totals.csv, data/careers.csv,
       data/bbref_draft.csv
Writes output/pick_curve.csv, output/colleges.csv, output/teams.csv,
       output/steals.csv

Run: .venv/bin/python python/05_analyze.py
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

WINDOW = (1989, 2015)
HIT_MINUTES = 10_000
MIN_DRAFTEES = 8
OUTCOMES = ["ws", "min", "vorp", "peak3"]


def fnum(s: str) -> float:
    return float(s) if s not in ("", None) else 0.0


def sample_sd(xs: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def pava_decreasing(picks: list[int], means: dict[int, float],
                    weights: dict[int, float]) -> dict[int, float]:
    """Weighted isotonic regression, constrained non-increasing in pick.
    Pool-adjacent-violators on the negated series."""
    blocks: list[list] = []  # [neg_mean, weight, [picks]]
    for p in picks:
        blocks.append([-means[p], weights[p], [p]])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            b = blocks.pop()
            a = blocks.pop()
            w = a[1] + b[1]
            blocks.append([(a[0] * a[1] + b[0] * b[1]) / w, w, a[2] + b[2]])
    fit = {}
    for neg, _, ps in blocks:
        for p in ps:
            fit[p] = -neg
    return fit


def load() -> list[dict]:
    minutes: dict[int, float] = {}
    with (DATA / "career_totals.csv").open() as f:
        for r in csv.DictReader(f):
            minutes[int(float(r["PLAYER_ID"]))] = fnum(r["MIN"])

    bbref: dict[tuple[int, int], dict] = {}
    with (DATA / "bbref_draft.csv").open() as f:
        for r in csv.DictReader(f):
            bbref[(int(r["year"]), int(r["pick"]))] = {
                "ws": fnum(r["ws"]), "vorp": fnum(r["vorp"])}

    # Per-season efficiency and per-franchise minutes from the season rows.
    # A multi-team season has a TOT row (TEAM_ID 0) carrying the season
    # totals; the team rows carry the franchise split.
    eff: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    eff_has_tot: dict[int, set] = defaultdict(set)
    team_min: dict[tuple[int, int], float] = defaultdict(float)
    with (DATA / "careers.csv").open() as f:
        for r in csv.DictReader(f):
            pid = int(r["PLAYER_ID"])
            season = r["SEASON_ID"]
            e = (fnum(r["PTS"]) + fnum(r["REB"]) + fnum(r["AST"])
                 + fnum(r["STL"]) + fnum(r["BLK"])
                 - (fnum(r["FGA"]) - fnum(r["FGM"]))
                 - (fnum(r["FTA"]) - fnum(r["FTM"])) - fnum(r["TOV"]))
            if r["TEAM_ABBREVIATION"] == "TOT":
                eff[pid][season] = e
                eff_has_tot[pid].add(season)
            else:
                if season not in eff_has_tot[pid]:
                    eff[pid][season] += e
                team_min[(pid, int(float(r["TEAM_ID"])))] += fnum(r["MIN"])

    def peak3(pid: int) -> float:
        seasons = [eff[pid][s] for s in sorted(eff[pid])]
        if not seasons:
            return 0.0
        if len(seasons) <= 3:
            return sum(seasons)
        return max(sum(seasons[i:i + 3]) for i in range(len(seasons) - 2))

    rows = []
    with (DATA / "draft_history.csv").open() as f:
        for r in csv.DictReader(f):
            pid = int(r["PERSON_ID"])
            year, pick = int(r["SEASON"]), int(r["OVERALL_PICK"])
            bb = bbref[(year, pick)]
            rows.append({
                "year": year, "pick": pick, "player": r["PLAYER_NAME"],
                "team_id": int(r["TEAM_ID"]),
                "team": f"{r['TEAM_CITY']} {r['TEAM_NAME']}".strip(),
                "org": r["ORGANIZATION"],
                "org_type": r["ORGANIZATION_TYPE"],
                "min": minutes.get(pid, 0.0),
                "kept_min": team_min.get((pid, int(r["TEAM_ID"])), 0.0),
                "ws": bb["ws"], "vorp": bb["vorp"],
                "peak3": peak3(pid),
            })
    return rows


def main() -> int:
    OUT.mkdir(exist_ok=True)
    rows = load()

    label: dict[int, str] = {}
    for r in sorted(rows, key=lambda r: (r["year"], r["pick"])):
        label[r["team_id"]] = r["team"]

    window = [r for r in rows if WINDOW[0] <= r["year"] <= WINDOW[1]]

    # ── Slot expectation: weighted isotonic fit per outcome ───────────────
    picks_present = sorted({r["pick"] for r in window})
    curves: dict[str, dict[int, float]] = {}
    counts = {p: sum(1 for r in window if r["pick"] == p)
              for p in picks_present}
    for oc in OUTCOMES:
        means = {p: (sum(r[oc] for r in window if r["pick"] == p)
                     / counts[p]) for p in picks_present}
        curves[oc] = pava_decreasing(picks_present, means,
                                     {p: float(counts[p])
                                      for p in picks_present})
    with (OUT / "pick_curve.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pick", "picks"] + [f"exp_{oc}" for oc in OUTCOMES])
        for p in picks_present:
            w.writerow([p, counts[p]]
                       + [round(curves[oc][p], 3) for oc in OUTCOMES])

    for r in window:
        for oc in OUTCOMES:
            r[f"v_{oc}"] = r[oc] - curves[oc][r["pick"]]

    # Era fairness: express WS value in within-class standard deviations.
    class_sd = {}
    by_class: dict[int, list[float]] = defaultdict(list)
    for r in window:
        by_class[r["year"]].append(r["v_ws"])
    for y, vs in by_class.items():
        class_sd[y] = sample_sd(vs)
    for r in window:
        r["v_ws_z"] = r["v_ws"] / class_sd[r["year"]]

    # ── Colleges ──────────────────────────────────────────────────────────
    colleges: dict[str, list[dict]] = defaultdict(list)
    for r in window:
        if r["org_type"] == "College/University":
            colleges[r["org"]].append(r)
    with (OUT / "colleges.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["college", "draftees", "hits", "hit_rate", "total_ws",
                    "value_ws", "value_ws_z", "value_vorp", "value_min"])
        table = []
        for org, ps in colleges.items():
            if len(ps) < MIN_DRAFTEES:
                continue
            hits = sum(1 for p in ps if p["min"] >= HIT_MINUTES)
            table.append([
                org, len(ps), hits, round(hits / len(ps), 3),
                round(sum(p["ws"] for p in ps), 1),
                round(sum(p["v_ws"] for p in ps), 1),
                round(sum(p["v_ws_z"] for p in ps), 2),
                round(sum(p["v_vorp"] for p in ps), 1),
                round(sum(p["v_min"] for p in ps), 1)])
        table.sort(key=lambda t: (-t[5], t[0]))
        w.writerows(table)

    # ── Teams ─────────────────────────────────────────────────────────────
    teams: dict[int, list[dict]] = defaultdict(list)
    for r in window:
        teams[r["team_id"]].append(r)
    with (OUT / "teams.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["team", "picks", "avg_pick", "hits", "total_ws",
                    "value_ws", "ci_lo", "ci_hi", "value_ws_z", "value_vorp",
                    "value_min", "kept_min", "kept_share"])
        table = []
        for tid, ps in teams.items():
            hits = sum(1 for p in ps if p["min"] >= HIT_MINUTES)
            vws = [p["v_ws"] for p in ps]
            total_v = sum(vws)
            half = 1.96 * sample_sd(vws) * math.sqrt(len(ps))
            total_min = sum(p["min"] for p in ps)
            kept = sum(p["kept_min"] for p in ps)
            table.append([
                label[tid], len(ps),
                round(sum(p["pick"] for p in ps) / len(ps), 1), hits,
                round(sum(p["ws"] for p in ps), 1),
                round(total_v, 1), round(total_v - half, 1),
                round(total_v + half, 1),
                round(sum(p["v_ws_z"] for p in ps), 2),
                round(sum(p["v_vorp"] for p in ps), 1),
                round(sum(p["v_min"] for p in ps), 1),
                round(kept, 1),
                round(kept / total_min, 3) if total_min else 0.0])
        table.sort(key=lambda t: (-t[5], t[0]))
        w.writerows(table)

    # ── Steals: careers furthest above their slot in Win Shares ───────────
    steals = sorted(window, key=lambda r: (-r["v_ws"], r["player"]))[:15]
    with (OUT / "steals.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["player", "year", "pick", "team", "college",
                    "ws", "expected_ws", "value_ws", "vorp"])
        for r in steals:
            w.writerow([r["player"], r["year"], r["pick"],
                        label[r["team_id"]], r["org"], round(r["ws"], 1),
                        round(curves["ws"][r["pick"]], 1),
                        round(r["v_ws"], 1), round(r["vorp"], 1)])

    print(f"window {WINDOW[0]}-{WINDOW[1]}: {len(window)} picks, "
          f"{len(teams)} franchises")
    for name in ("pick_curve", "colleges", "teams", "steals"):
        print(f"wrote output/{name}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
