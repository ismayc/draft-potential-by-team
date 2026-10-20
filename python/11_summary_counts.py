"""Write output/summary_counts.csv: the counts the README and story quote
that no analysis table holds (rows in the harvested source files, and how
many franchise intervals cross zero), so each prose number has a committed
cell to bind to.

The crossing count is read from output/teams.csv, which the reconcile gate
already holds equal across Python and R, so no separate R twin is needed.
The two row counts are plain line counts of committed harvest files.

Run:   .venv/bin/python python/11_summary_counts.py
Check: .venv/bin/python python/11_summary_counts.py --check
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"
TARGET = OUT / "summary_counts.csv"


def n_rows(path: Path) -> int:
    with path.open(newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def build() -> list[list[str]]:
    with (OUT / "teams.csv").open(newline="") as f:
        teams = list(csv.DictReader(f))
    crossing = sum(1 for t in teams
                   if float(t["ci_lo"]) <= 0 <= float(t["ci_hi"]))
    return [["metric", "value"],
            ["draft_history_picks", str(n_rows(DATA / "draft_history.csv"))],
            ["lottery_rows", str(n_rows(DATA / "lottery.csv"))],
            ["franchises_crossing_zero", str(crossing)]]


def render(rows: list[list[str]]) -> str:
    return "".join(",".join(r) + "\n" for r in rows)


def main(argv: list[str]) -> int:
    text = render(build())
    if "--check" in argv:
        if not TARGET.exists() or TARGET.read_text() != text:
            print("summary_counts.csv is stale: rerun python/11_summary_counts.py",
                  file=sys.stderr)
            return 1
        print("summary_counts.csv matches a fresh count")
        return 0
    OUT.mkdir(exist_ok=True)
    TARGET.write_text(text)
    print(f"wrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
