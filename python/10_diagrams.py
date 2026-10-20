"""Explainer diagrams for the analysis page (docs/story.md), drawn with the
family's famdiagram (theme-aware SVG, colors as classes only; the page
builder inlines them). Every number is read from the committed output
tables, the same ones the reconcile gate holds equal to the R build, or
from 05_analyze.py's own settings:

  dg1_method      how a pick becomes value and how values roll up: every
                  pick in the window, the slot price, value = career minus
                  price, then franchises, colleges, and steals
                  (output/pick_curve.csv, 05_analyze.py settings)
  dg2_steals      every steal in the table as a dumbbell from the slot's
                  price to the career; the line's length is the value above
                  slot (output/steals.csv)
  dg3_intervals   every franchise's value with its 95% interval against
                  zero, the ones that clear it marked (output/teams.csv)

famdiagram lives in the family tools repo, found at $BBA_TOOLS or the
sibling folder ../basketball-analysis-tools (CI checks the tools repo out
and sets BBA_TOOLS).

Run:  .venv/bin/python python/10_diagrams.py          (writes figures/dg*.svg)
      .venv/bin/python python/10_diagrams.py --check  (fails if a committed
                                                       SVG differs from a
                                                       fresh build)
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
FIGS = ROOT / "figures"
TOOLS = Path(os.environ.get("BBA_TOOLS", ROOT.parent / "basketball-analysis-tools"))
sys.path.insert(0, str(TOOLS))
import famdiagram as fd  # noqa: E402

_spec = importlib.util.spec_from_file_location("draft_analyze_settings",
                                               ROOT / "python" / "05_analyze.py")
ANALYZE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ANALYZE)

def rows(name: str) -> list[dict]:
    with (OUT / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def signed(x: float) -> str:
    return f"{x:+,.0f}".replace("-", "−")


# ---------------------------------------------------------------------------
# 1. The method
# ---------------------------------------------------------------------------

def dg_method(layout: str) -> fd.Diagram:
    curve = rows("pick_curve")
    picks = sum(int(r["picks"]) for r in curve)
    first, last = curve[0], curve[-1]
    lo, hi = ANALYZE.WINDOW
    p1, pn = float(first["exp_ws"]), float(last["exp_ws"])
    title = (f"How the analysis prices a pick and scores who drafted it: {picks:,} picks "
             f"from the {lo}-{hi} classes")
    steps = [
        ("1", f"{picks:,} picks", [f"classes {lo}-{hi}, each with", "ten full NBA seasons"]),
        ("2", "Price each slot", ["average career Win Shares by", "pick, never rising with a",
                                  f"later pick: {p1:.0f} at pick {first['pick']},",
                                  f"{pn:.0f} at pick {last['pick']}"]),
        ("3", "Score each pick", ["career Win Shares minus", "its slot's price"]),
    ]
    rollups = [
        ("Franchises", ["sum of their picks' scores,", "with a 95% interval"]),
        ("Colleges", [f"{ANALYZE.MIN_DRAFTEES}+ draftees; a hit is a", f"career of "
                      f"{ANALYZE.HIT_MINUTES:,}+ minutes"]),
        ("Steals", ["single picks furthest", "above their price"]),
    ]
    foot = "Python and R each build every table; the reconcile gate holds them equal."
    if layout == "wide":
        W, H, s = 760, 326, 14
        d = fd.Diagram(W, H, title)
        bw, bh, gap, y = 220, 132, 30, 16
        for i, (num, head, body) in enumerate(steps):
            x = 16 + i * (bw + gap)
            d.rect(x, y, bw, bh, fill="surface2", stroke="rule", sw=1, rx=6)
            d.circle(x + 22, y + 24, 12, fill="accent")
            d.text(x + 22, y + 29, num, size=s, fill="surface", anchor="middle", weight="700")
            d.text(x + 42, y + 30, head, size=s + 2, weight="600")
            for j, line in enumerate(body):
                d.text(x + 14, y + 58 + j * (s + 6), line, size=s, fill="ink2")
            if i < 2:
                d.line(x + bw + 3, y + bh / 2, x + bw + gap - 3, y + bh / 2, stroke="ink3",
                       sw=1.6, arrow=True)
        ry = y + bh + 60
        xs = 16 + 2 * (bw + gap) + bw / 2
        for i, (head, body) in enumerate(rollups):
            x = 16 + i * (bw + gap)
            d.path(f"M{xs:.1f},{y + bh} C{xs:.1f},{y + bh + 34} {x + bw / 2:.1f},"
                   f"{ry - 34} {x + bw / 2:.1f},{ry - 4}", stroke="ink3", sw=1.3, arrow=True)
            d.rect(x, ry, bw, 78, fill="surface", stroke="nba", sw=1.5, rx=6)
            d.text(x + 14, ry + 26, head, size=s + 2, weight="600", fill="nba")
            for j, line in enumerate(body):
                d.text(x + 14, ry + 48 + j * (s + 5), line, size=s, fill="ink2")
        d.text(16, H - 14, foot, size=s, fill="ink3")
    else:
        W, s = 360, 13
        d = fd.Diagram(W, 0, title)
        y = 12
        for i, (num, head, body) in enumerate(steps):
            bh = 46 + len(body) * (s + 5)
            d.rect(12, y, W - 24, bh, fill="surface2", stroke="rule", sw=1, rx=6)
            d.circle(34, y + 22, 11, fill="accent")
            d.text(34, y + 27, num, size=s, fill="surface", anchor="middle", weight="700")
            d.text(54, y + 28, head, size=s + 2, weight="600")
            for j, line in enumerate(body):
                d.text(26, y + 52 + j * (s + 5), line, size=s, fill="ink2")
            y += bh
            d.line(W / 2, y + 2, W / 2, y + 22, stroke="ink3", sw=1.5, arrow=True)
            y += 26
        for head, body in rollups:
            bh = 38 + len(body) * (s + 5)
            d.rect(12, y, W - 24, bh, fill="surface", stroke="nba", sw=1.5, rx=6)
            d.text(26, y + 24, head, size=s + 2, weight="600", fill="nba")
            for j, line in enumerate(body):
                d.text(26, y + 44 + j * (s + 5), line, size=s, fill="ink2")
            y += bh + 10
        d.text(12, y + 14, "Python and R each build every table;", size=s, fill="ink3")
        d.text(12, y + 32, "the reconcile gate holds them equal.", size=s, fill="ink3")
        d.h = y + 44
    return d


# ---------------------------------------------------------------------------
# 2. Every steal, as a dumbbell from price to career
# ---------------------------------------------------------------------------

def dg_steals(layout: str) -> fd.Diagram:
    steals = sorted(rows("steals"), key=lambda r: -float(r["value_ws"]))
    top = max(float(r["ws"]) for r in steals)
    step = 50
    x_hi = int(-(-top // step)) * step
    title = (f"The {len(steals)} biggest steals as dumbbells: each line runs from the "
             f"slot's price to the career, and its length is the value above slot")
    wide = layout == "wide"
    W, s = (760, 14) if wide else (360, 12)
    lab_w = 230 if wide else 150
    val_w = 56 if wide else 40
    rh = 24 if wide else 21
    top_y = 58
    px0, px1 = 16 + lab_w, W - 16 - val_w
    H = top_y + len(steals) * rh + 50
    d = fd.Diagram(W, H, title)

    def X(v: float) -> float:
        return px0 + v / x_hi * (px1 - px0)

    d.circle(22, 24, 5.5, fill="ink3")
    d.text(32, 29, "slot's price", size=s, fill="ink2")
    d.circle(132 if wide else 122, 24, 5.5, fill="nba")
    d.text(142 if wide else 132, 29, "career Win Shares", size=s, fill="ink2")
    d.text(W - 16, 29, "above slot", size=s, fill="ink3", anchor="end")
    for v in range(0, x_hi + 1, step):
        d.line(X(v), top_y - 8, X(v), top_y + len(steals) * rh, stroke="rule",
               sw=1.6 if v == 0 else 1)
        if wide or v % 100 == 0:
            d.text(X(v), top_y + len(steals) * rh + s + 6, f"{v}", size=s, fill="ink3",
                   anchor="middle")
    for i, r in enumerate(steals):
        y = top_y + i * rh + rh / 2
        price, ws = float(r["expected_ws"]), float(r["ws"])
        name = r["player"]
        if not wide and len(name) > 14:
            first, *rest = name.split()
            name = f"{first[0]}. {' '.join(rest)}"
        d.text(px0 - 10, y + s * 0.35, f"{name}, pick {r['pick']}", size=s, anchor="end",
               fill="ink2")
        d.line(X(price), y, X(ws), y, stroke="nba", sw=3, opacity=0.55)
        d.circle(X(price), y, 5, fill="ink3")
        d.circle(X(ws), y, 5, fill="nba")
        d.text(W - 16, y + s * 0.35, signed(float(r["value_ws"])), size=s, anchor="end",
               weight="600", fill="nba")
    d.text((px0 + px1) / 2, H - 10, "career Win Shares", size=s, fill="ink3",
           anchor="middle")
    return d


# ---------------------------------------------------------------------------
# 3. Franchise intervals
# ---------------------------------------------------------------------------

def dg_intervals(layout: str) -> fd.Diagram:
    teams = sorted(rows("teams"), key=lambda r: -float(r["value_ws"]))
    cross = [t for t in teams if float(t["ci_lo"]) <= 0 <= float(t["ci_hi"])]
    lo = min(float(t["ci_lo"]) for t in teams)
    hi = max(float(t["ci_hi"]) for t in teams)
    step = 250
    lo_t, hi_t = (int(lo // step) * step), (int(-(-hi // step)) * step)
    title = (f"Every franchise's Win Shares above slot with its 95% interval: {len(cross)} "
             f"of {len(teams)} intervals cross zero")
    wide = layout == "wide"
    W, s = (760, 14) if wide else (360, 12)
    lab_w = 200 if wide else 156
    rh = 19 if wide else 16
    top = 64
    px0, px1 = 16 + lab_w, W - (40 if wide else 24)
    H = top + len(teams) * rh + 52
    d = fd.Diagram(W, H, title)

    def X(v: float) -> float:
        return px0 + (v - lo_t) / (hi_t - lo_t) * (px1 - px0)

    d.text(16, 20, f"{len(cross)} of {len(teams)} intervals cross zero", size=s + 2,
           weight="600")
    d.line(16, 40, 30, 40, stroke="nba", sw=2)
    d.text(36, 44, "crosses zero", size=s, fill="ink2")
    d.line(140 if wide else 132, 40, 154 if wide else 146, 40, stroke="c8", sw=2.4)
    d.text(160 if wide else 152, 44, "clear of zero", size=s, fill="ink2")
    for v in range(lo_t, hi_t + 1, step):
        d.line(X(v), top - 6, X(v), top + len(teams) * rh, stroke="rule",
               sw=1.6 if v == 0 else 1)
        if wide or v % 500 == 0:
            d.text(X(v), top + len(teams) * rh + s + 6, signed(v) if v else "0", size=s,
                   fill="ink3", anchor="middle")
    for i, t in enumerate(teams):
        y = top + i * rh + rh / 2
        c = "nba" if t in cross else "c8"
        d.text(px0 - 8, y + s * 0.35, t["team"], size=s, anchor="end",
               fill="ink" if t not in cross else "ink2", weight=None if t in cross else "600")
        d.line(X(float(t["ci_lo"])), y, X(float(t["ci_hi"])), y, stroke=c,
               sw=2 if t in cross else 2.4, opacity=0.75 if t in cross else None)
        d.circle(X(float(t["value_ws"])), y, 3.4, fill=c)
    d.text((px0 + px1) / 2, H - 10, "Win Shares above slot expectation", size=s, fill="ink3",
           anchor="middle")
    return d


BUILDERS = {"dg1_method": dg_method, "dg2_steals": dg_steals,
            "dg3_intervals": dg_intervals}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    fails = []
    for ref, build in BUILDERS.items():
        wide, narrow = build("wide"), build("narrow")
        if args.check:
            for dg, name in ((wide, f"{ref}.svg"), (narrow, f"{ref}_narrow.svg")):
                p = FIGS / name
                if not p.exists() or p.read_text() != dg.svg():
                    fails.append(name)
        else:
            for p in fd.save(FIGS, ref, wide, narrow):
                print(f"wrote figures/{p.name}")
    if args.check:
        for f in fails:
            print("FAIL", f, "differs from a fresh build")
        print("DIAGRAMS", "FAILED" if fails else f"PASSED: {len(BUILDERS)} diagrams")
        return 1 if fails else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
