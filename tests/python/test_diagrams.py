"""Tests for 10_diagrams: the analysis page's explainer diagrams.

The diagrams print numbers read from the committed output tables, so the
tests check those numbers against the same CSVs, the rule that picks the
three steals, the interval count the story states, the colors-as-classes
contract, and the --check mode that run_checks and CI rely on.
"""
import csv
import re

import pytest

from conftest import ROOT, load_script

mod10 = load_script("10_diagrams")


def _rows(name):
    with (ROOT / "output" / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


@pytest.fixture()
def figs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mod10, "FIGS", tmp_path)
    return tmp_path


@pytest.mark.parametrize("ref", list(mod10.BUILDERS))
@pytest.mark.parametrize("layout", ["wide", "narrow"])
def test_every_diagram_uses_classes_not_hex(ref, layout):
    svg = mod10.BUILDERS[ref](layout).svg()
    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg" class="dg"')
    assert not re.search(r"#[0-9a-fA-F]{6}\b", svg)
    width = 760 if layout == "wide" else 360
    assert f'viewBox="0 0 {width} ' in svg


def test_method_reads_the_pick_curve_and_settings():
    curve = _rows("pick_curve")
    total = sum(int(r["picks"]) for r in curve)
    for layout in ("wide", "narrow"):
        svg = mod10.dg_method(layout).svg()
        assert f"{total:,} picks" in svg
        assert f"{float(curve[0]['exp_ws']):.0f} at pick 1," in svg
        assert f"{float(curve[-1]['exp_ws']):.0f} at pick 60" in svg
        assert f"{mod10.ANALYZE.HIT_MINUTES:,}+ minutes" in svg
        lo, hi = mod10.ANALYZE.WINDOW
        assert f"classes {lo}-{hi}" in svg


def test_steals_dumbbell_has_every_steal_in_value_order():
    steals = sorted(_rows("steals"), key=lambda r: -float(r["value_ws"]))
    for layout in ("wide", "narrow"):
        svg = mod10.dg_steals(layout).svg()
        assert f"The {len(steals)} biggest steals" in svg
        values = [mod10.signed(float(r["value_ws"])) for r in steals]
        pos = [svg.index(f">{v}<") for v in values]
        assert pos == sorted(pos)
        for r in steals:
            assert f", pick {r['pick']}<" in svg
        # two dots per steal plus the two legend dots
        assert svg.count("<circle") == 2 * len(steals) + 2
    wide = mod10.dg_steals("wide").svg()
    narrow = mod10.dg_steals("narrow").svg()
    for r in steals:
        shown = r["player"].replace("'", "&#x27;")
        assert f">{shown}, pick" in wide
    # long names are shortened on phones, short ones kept
    assert ">S. O&#x27;Neal, pick 1<" in narrow
    assert ">LeBron James, pick 1<" in narrow


def test_intervals_count_matches_the_teams_table():
    teams = _rows("teams")
    cross = sum(float(t["ci_lo"]) <= 0 <= float(t["ci_hi"]) for t in teams)
    for layout in ("wide", "narrow"):
        svg = mod10.dg_intervals(layout).svg()
        assert f"{cross} of {len(teams)} intervals cross zero" in svg
        for t in teams:
            assert t["team"].replace("'", "&#x27;") in svg
    assert svg.count('class="dg-f-c8"') == len(teams) - cross


def test_signed_uses_a_minus_sign():
    assert mod10.signed(-394.3) == "−394"
    assert mod10.signed(1000) == "+1,000"


def test_main_writes_then_checks(figs_dir, capsys):
    assert mod10.main([]) == 0
    names = sorted(p.name for p in figs_dir.glob("*.svg"))
    assert names == sorted(f"{r}{s}.svg" for r in mod10.BUILDERS for s in ("", "_narrow"))
    assert mod10.main(["--check"]) == 0
    assert "PASSED" in capsys.readouterr().out


def test_check_fails_on_a_stale_or_missing_svg(figs_dir, capsys):
    mod10.main([])
    (figs_dir / "dg1_method.svg").write_text("<svg/>")
    (figs_dir / "dg2_steals_narrow.svg").unlink()
    assert mod10.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert "FAIL dg1_method.svg" in out
    assert "FAIL dg2_steals_narrow.svg" in out


def test_committed_svgs_are_current():
    assert mod10.main(["--check"]) == 0
