"""Rewrite README.md's Findings section from the committed output tables.

No analysis number in the README is typed by hand: this script owns
everything between the findings markers, so the prose can never drift from
the CSVs it summarises. Run after 05/06.

Run: .venv/bin/python python/07_findings.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
README = ROOT / "README.md"

START = "<!-- findings:start -->"
END = "<!-- findings:end -->"


def rows(name: str) -> list[dict]:
    with (OUT / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def fmt(n: str | float) -> str:
    return f"{float(n):,.0f}"


def build() -> str:
    curve = rows("pick_curve")
    colleges = rows("colleges")
    teams = rows("teams")
    steals = rows("steals")

    first, last = curve[0], curve[-1]
    zero_cross = sum(1 for t in teams
                     if float(t["ci_lo"]) <= 0 <= float(t["ci_hi"]))
    lines = [
        START,
        "",
        "Draft classes 1989-2015 (every class with ten full NBA seasons to",
        "accumulate a career). The headline outcome is career Win Shares",
        "(Basketball-Reference); value is WS above the expectation for the",
        "pick slot, where the expectation curve is a weighted isotonic fit",
        "over picks 1-60 — no buckets, no functional form.",
        "",
        f"- The slot gradient: pick 1 carries an expectation of",
        f"  {fmt(first['exp_ws'])} career Win Shares; pick 60 carries"
        f" {fmt(last['exp_ws'])}.",
        "",
        "**Colleges producing the most NBA value** (8+ draftees; hits are",
        "careers of 10,000+ minutes):",
        "",
        "| College | Draftees | Hits | Hit rate | WS above slot |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in colleges[:5]:
        lines.append(
            f"| {c['college']} | {c['draftees']} | {c['hits']} | "
            f"{float(c['hit_rate']):.0%} | +{fmt(c['value_ws'])} |")
    best_rate = max((c for c in colleges if int(c["draftees"]) >= 15),
                    key=lambda c: float(c["hit_rate"]))
    lines += [
        "",
        f"Among colleges with 15+ draftees, {best_rate['college']} has the",
        f"best hit rate: {best_rate['hits']} of {best_rate['draftees']}",
        f"picks ({float(best_rate['hit_rate']):.0%}) became 10,000-minute",
        "NBA players.",
        "",
        "**Teams drafting the best, relative to where they picked** (the",
        "95% interval is a normal approximation on the team's pick values;",
        "kept share is the fraction of drafted careers' minutes played for",
        "the drafting franchise):",
        "",
        "| Franchise | Picks | Avg pick | WS above slot | 95% interval "
        "| Kept share |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for t in teams[:5]:
        lines.append(
            f"| {t['team']} | {t['picks']} | {t['avg_pick']} | "
            f"+{fmt(t['value_ws'])} | {fmt(t['ci_lo'])} to "
            f"{fmt(t['ci_hi'])} | {float(t['kept_share']):.0%} |")
    worst = teams[-1]
    keeper = max(teams, key=lambda t: float(t["kept_share"]))
    lines += [
        "",
        f"The {worst['team']} sit last ({fmt(worst['value_ws'])} WS against",
        f"slot expectation). Draft value is heavy-tailed: {zero_cross} of 30",
        "franchise intervals cross zero, so most of the league is",
        "statistically indistinguishable on drafting skill — the ordering",
        "is the estimate, not a verdict. The",
        f"{keeper['team']} kept the largest share of the careers they",
        f"drafted ({float(keeper['kept_share']):.0%} of minutes).",
        "",
        "**The biggest steals** (career WS furthest above the pick's slot",
        "expectation):",
        "",
        "| Player | Year | Pick | Drafted by | WS above slot |",
        "| --- | --- | --- | --- | --- |",
    ]
    for s in steals[:5]:
        lines.append(
            f"| {s['player']} | {s['year']} | {s['pick']} | {s['team']} | "
            f"+{fmt(s['value_ws'])} |")
    lines += [
        "",
        "Full tables: `output/colleges.csv`, `output/teams.csv`,",
        "`output/steals.csv`, `output/pick_curve.csv` — each with VORP,",
        "career-minutes, and within-class-z companion columns, and each",
        "mirrored by an `_r.csv` twin from the independent R implementation",
        "(the reconcile gate holds them equal).",
        "",
        END,
    ]
    return "\n".join(lines)


def main() -> int:
    text = README.read_text()
    if START not in text:
        raise SystemExit("findings markers not found in README.md")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    README.write_text(head + build() + tail)
    print("rewrote README.md findings section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
