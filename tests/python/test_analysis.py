"""Invariants of the Python analysis outputs (output/*.csv)."""
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "output"


def rows(name):
    with (OUT / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def test_value_added_is_zero_sum_across_teams():
    # Value is measured against bucket means computed on the same picks,
    # so across all 30 franchises it must cancel to ~0 (rounding aside).
    total = sum(float(t["value_added"]) for t in rows("teams"))
    assert abs(total) < 5.0
    assert len(rows("teams")) == 30


def test_pick_curve_declines_monotonically():
    means = [float(r["mean_min"]) for r in rows("pick_curve")]
    assert means == sorted(means, reverse=True)
    assert len(means) == 7


def test_college_hit_rates_are_consistent():
    for c in rows("colleges"):
        draftees, hits = int(c["draftees"]), int(c["hits"])
        assert 0 <= hits <= draftees
        assert draftees >= 8
        assert abs(float(c["hit_rate"]) - round(hits / draftees, 3)) < 1e-9


def test_steals_are_positive_and_ranked():
    values = [float(s["value_added"]) for s in rows("steals")]
    assert len(values) == 15
    assert all(v > 0 for v in values)
    assert values == sorted(values, reverse=True)
