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


def fmt(n: str) -> str:
    return f"{float(n):,.0f}"


def build() -> str:
    curve = rows("pick_curve")
    colleges = rows("colleges")
    teams = rows("teams")
    steals = rows("steals")

    top = curve[0]
    bottom = curve[-1]
    lines = [
        START,
        "",
        "Draft classes 1989-2015 (every class with ten full NBA seasons to",
        "accumulate a career), value measured in career regular-season",
        "minutes relative to the mean for the pick's slot bucket.",
        "",
        f"- The slot gradient is steep: picks {top['bucket']} average",
        f"  {fmt(top['mean_min'])} career minutes; picks {bottom['bucket']}"
        f" average {fmt(bottom['mean_min'])}",
        f"  ({float(top['mean_min']) / float(bottom['mean_min']):.0f}x).",
        "",
        "**Colleges producing the most NBA talent** (8+ draftees; hits are",
        f"careers of 10,000+ minutes):",
        "",
        "| College | Draftees | Hits | Hit rate | Minutes above slot |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in colleges[:5]:
        lines.append(
            f"| {c['college']} | {c['draftees']} | {c['hits']} | "
            f"{float(c['hit_rate']):.0%} | +{fmt(c['value_added'])} |")
    best_rate = max((c for c in colleges if int(c["draftees"]) >= 15),
                    key=lambda c: float(c["hit_rate"]))
    lines += [
        "",
        f"Among colleges with 15+ draftees, {best_rate['college']} has the",
        f"best hit rate: {best_rate['hits']} of {best_rate['draftees']}",
        f"picks ({float(best_rate['hit_rate']):.0%}) became 10,000-minute",
        "NBA players.",
        "",
        "**Teams drafting the best, relative to where they picked**:",
        "",
        "| Franchise | Picks | Avg pick | Hits | Minutes above slot |",
        "| --- | --- | --- | --- | --- |",
    ]
    for t in teams[:5]:
        lines.append(
            f"| {t['team']} | {t['picks']} | {t['avg_pick']} | {t['hits']} | "
            f"+{fmt(t['value_added'])} |")
    worst = teams[-1]
    lines += [
        "",
        f"At the other end, the {worst['team']} sit last: "
        f"{fmt(worst['value_added'])} minutes against slot expectation "
        f"across {worst['picks']} picks.",
        "",
        "**The biggest steals** (career minutes furthest above the pick's",
        "slot mean):",
        "",
        "| Player | Year | Pick | Drafted by | Minutes above slot |",
        "| --- | --- | --- | --- | --- |",
    ]
    for s in steals[:5]:
        lines.append(
            f"| {s['player']} | {s['year']} | {s['pick']} | {s['team']} | "
            f"+{fmt(s['value_added'])} |")
    lines += [
        "",
        "Full tables: `output/colleges.csv`, `output/teams.csv`,",
        "`output/steals.csv`, `output/pick_curve.csv` (each mirrored by an",
        "`_r.csv` twin from the independent R implementation; the reconcile",
        "gate holds them equal).",
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
