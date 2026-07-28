"""Reconcile the Python and R analysis outputs.

Every table must agree row for row: same shape, same key order, numeric
cells within 1e-6, text cells identical. Any disagreement is a non-zero
exit — the two implementations are only trustworthy together.

Run: .venv/bin/python python/06_reconcile.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"

TABLES = ["pick_curve", "colleges", "teams", "steals"]
TOL = 1e-6


def read(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open() as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def compare(name: str) -> list[str]:
    header_py, py = read(OUT / f"{name}.csv")
    header_r, r = read(OUT / f"{name}_r.csv")
    problems = []
    if header_py != header_r:
        return [f"{name}: headers differ: {header_py} vs {header_r}"]
    if len(py) != len(r):
        return [f"{name}: {len(py)} rows (py) vs {len(r)} rows (R)"]
    for i, (rowp, rowr) in enumerate(zip(py, r)):
        for col, (a, b) in zip(header_py, zip(rowp, rowr)):
            try:
                ok = abs(float(a) - float(b)) <= TOL
            except ValueError:
                ok = a == b
            if not ok:
                problems.append(f"{name} row {i + 1} [{col}]: {a!r} != {b!r}")
    return problems


def main() -> int:
    problems: list[str] = []
    for name in TABLES:
        problems += compare(name)
    if problems:
        print("RECONCILE FAILURES:", file=sys.stderr)
        for p in problems[:40]:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"reconciled: {', '.join(TABLES)} — Python and R agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
