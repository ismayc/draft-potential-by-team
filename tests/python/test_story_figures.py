"""Tests for 09_story_figures: the analysis-page figure emitter.

The figures embed the committed output tables verbatim, so the tests
assert against the same CSVs the page claims to be built from, and pin
the write_html-compatible structure the family page builder rewrites
(the plotly CDN script tag it swaps for famplot, the graph div, the
responsive config).
"""
import csv
import json

import pytest

from conftest import ROOT, load_script

mod09 = load_script("09_story_figures")


@pytest.fixture()
def figs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mod09, "FIGS", tmp_path)
    return tmp_path


def _read(figs_dir, name):
    return (figs_dir / f"{name}.html").read_text()


# ── write(): template structure and layout merging ──────────────────────


def test_write_emits_the_builder_compatible_shell(figs_dir):
    mod09.write("t", [{"type": "bar", "x": [1], "y": [2]}],
                {"height": 320, "xaxis": {"tickformat": ".0%"}})
    html = _read(figs_dir, "t")
    assert '<meta charset="utf-8" />' in html
    assert 'src="https://cdn.plot.ly/plotly-3.7.0.min.js"' in html
    assert 'class="plotly-graph-div"' in html
    assert '{"responsive": true}' in html
    assert 'style="height:320px; width:900px;"' in html
    # nested axis options merge into the base layout instead of replacing it
    assert '"tickformat": ".0%"' in html
    assert '"gridcolor": "#e1e0d9"' in html
    assert '"paper_bgcolor": "#fcfcfb"' in html


def test_write_is_deterministic(figs_dir):
    spec = [{"type": "scatter", "x": [1, 2], "y": [3, 4]}]
    mod09.write("t", spec, {})
    first = _read(figs_dir, "t")
    mod09.write("t", spec, {})
    assert _read(figs_dir, "t") == first


# ── the three figures against the committed tables ──────────────────────


def _rows(name):
    with (ROOT / "output" / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def test_slot_curve_embeds_every_pick(figs_dir):
    mod09.fig1_slot_curve()
    html = _read(figs_dir, "fig1_slot_curve")
    curve = _rows("pick_curve")
    assert f'"x": {json.dumps([int(r["pick"]) for r in curve])}' in html
    first = round(float(curve[0]["exp_ws"]), 1)
    assert json.dumps(first) in html
    assert '"color": "#2a78d6"' in html
    assert "expected career Win Shares" in html


def test_franchises_carry_intervals_for_all_30(figs_dir):
    mod09.fig2_franchises()
    html = _read(figs_dir, "fig2_franchises")
    teams = _rows("teams")
    assert len(teams) == 30
    for t in teams:
        assert json.dumps(t["team"]) in html
    top = max(teams, key=lambda r: float(r["value_ws"]))
    assert json.dumps([round(float(top["ci_lo"])), round(float(top["ci_hi"])),
                       top["picks"],
                       round(float(top["kept_share"]) * 100)]) in html
    assert '"autorange": "reversed"' in html
    assert "95%% interval" in html


def test_colleges_top_twelve_by_value(figs_dir):
    mod09.fig3_colleges()
    html = _read(figs_dir, "fig3_colleges")
    colleges = sorted(_rows("colleges"),
                      key=lambda r: -float(r["value_ws"]))
    for c in colleges[:12]:
        assert json.dumps(c["college"]) in html
    assert json.dumps(colleges[13]["college"]) not in html
    assert '"color": "#eb6834"' in html
