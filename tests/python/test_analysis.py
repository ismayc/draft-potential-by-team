"""Invariants of the Python analysis outputs (output/*.csv)."""
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "output"


def rows(name):
    with (OUT / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def test_ws_value_is_zero_sum_across_teams():
    # The isotonic fit preserves the weighted mean, so value above slot
    # summed over all 30 franchises must cancel to ~0 (rounding aside).
    total = sum(float(t["value_ws"]) for t in rows("teams"))
    assert abs(total) < 5.0
    assert len(rows("teams")) == 30


def test_pick_curves_decline_monotonically():
    curve = rows("pick_curve")
    assert len(curve) == 60
    for col in ("exp_ws", "exp_min", "exp_vorp", "exp_peak3"):
        means = [float(r[col]) for r in curve]
        assert all(a >= b for a, b in zip(means, means[1:])), col


def test_confidence_intervals_bracket_the_estimate():
    for t in rows("teams"):
        assert float(t["ci_lo"]) <= float(t["value_ws"]) <= float(t["ci_hi"])


def test_kept_minutes_are_a_valid_share():
    for t in rows("teams"):
        assert 0.0 <= float(t["kept_share"]) <= 1.0
        assert float(t["kept_min"]) >= 0.0


def test_college_hit_rates_are_consistent():
    for c in rows("colleges"):
        draftees, hits = int(c["draftees"]), int(c["hits"])
        assert 0 <= hits <= draftees
        assert draftees >= 8
        assert abs(float(c["hit_rate"]) - round(hits / draftees, 3)) < 1e-9


def test_steals_are_positive_and_ranked():
    values = [float(s["value_ws"]) for s in rows("steals")]
    assert len(values) == 15
    assert all(v > 0 for v in values)
    assert values == sorted(values, reverse=True)
