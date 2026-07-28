"""Tests for the pipeline scripts: parsers against the committed raw HTML,
gate failure paths, corrections, reconcile arithmetic, generator
determinism, and findings rewriting. Network I/O is pragma-excluded from
coverage and exercised by the real harvest runs instead."""
import csv
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT, load_script

mod01 = load_script("01_harvest_draft_history")
mod02 = load_script("02_harvest_lottery")
mod03 = load_script("03_harvest_careers")
mod04 = load_script("04_generate_site_data")
mod06 = load_script("06_reconcile")
mod07 = load_script("07_findings")
mod08 = load_script("08_harvest_bbref")


# ── 02: lottery parser against committed pages ──────────────────────────


def test_lottery_parser_reads_the_td_header_era():
    rows = mod02.parse_year(1993)
    assert len(rows) == 11
    first = rows[0]
    assert (first["team"], first["odds_pct"], first["seed_delta"],
            first["player_picked"]) == ("Orlando", 1.5, 10, "Chris Webber")
    assert first["pre_lottery_seed"] == 11


def test_lottery_parser_reads_the_th_header_era():
    rows = mod02.parse_year(1999)
    assert len(rows) == 13
    assert rows[0]["team"] == "Chicago"
    assert rows[2]["player_picked"] == "Baron Davis"
    assert rows[2]["seed_delta"] == 10  # Charlotte's 0.5% jump


def test_lottery_parser_fails_loudly_on_unrecognised_html(tmp_path,
                                                          monkeypatch):
    (tmp_path / "1993.html").write_text("<html><body>nope</body></html>")
    monkeypatch.setattr(mod02, "RAW", tmp_path)
    with pytest.raises(AssertionError):
        mod02.parse_year(1993)


def test_expected_teams_matches_the_era_boundaries():
    assert [mod02.expected_teams(y) for y in
            (1989, 1990, 1994, 1995, 2003, 2004, 2025)] == \
        [9, 11, 11, 13, 13, 14, 14]


def test_gate_catches_structural_problems():
    picks = {(1993, 1): "Chris Webber"}
    rows = [{"year": 1993, "result_position": 1, "team": "Orlando",
             "record_w": 41, "record_l": 41, "odds_pct": 50.0,
             "seed_delta": 0, "pre_lottery_seed": 99,
             "player_picked": "Somebody Else"}]
    problems = mod02.gate(1993, rows, picks, {})
    text = "\n".join(problems)
    assert "rows, expected" in text          # wrong team count
    assert "seeds out of range" in text
    assert "odds sum" in text
    assert "Somebody Else" in text           # name mismatch vs draft history


def test_gate_catches_position_gaps():
    base = {"year": 2004, "team": "T", "record_w": 30, "record_l": 52,
            "odds_pct": 50.0, "seed_delta": 0, "player_picked": "X"}
    rows = [dict(base, result_position=p, pre_lottery_seed=p)
            for p in (1, 3)]
    assert any("positions not contiguous" in p
               for p in mod02.gate(2004, rows, {}, {}))


def test_lottery_main_fails_when_a_gate_trips(monkeypatch, capsys):
    monkeypatch.setattr(mod02, "gate",
                        lambda year, rows, picks, aliases: [f"{year}: boom"])
    assert mod02.main() == 1
    assert "GATE FAILURES" in capsys.readouterr().err


def test_gate_catches_impossible_records_but_allows_expansion_zeros():
    picks = {}
    base = {"year": 2004, "odds_pct": 100.0, "seed_delta": 0,
            "player_picked": "X"}
    rows = [dict(base, result_position=i + 1, pre_lottery_seed=i + 1,
                 team=f"T{i}", record_w=30, record_l=52) for i in range(14)]
    rows[0].update(record_w=60, record_l=62)   # impossible
    rows[1].update(record_w=0, record_l=0)     # expansion: allowed
    problems = mod02.gate(2004, rows, picks, {})
    assert any("impossible record 60-62" in p for p in problems)
    assert not any("T1" in p for p in problems)


def test_gate_applies_aliases():
    picks = {(1993, 1): "Anfernee Hardaway"}
    rows = [{"year": 1993, "result_position": 1, "team": "Orlando",
             "record_w": 41, "record_l": 41, "odds_pct": 100.0,
             "seed_delta": 0, "pre_lottery_seed": 1,
             "player_picked": "Penny Hardaway"}]
    problems = mod02.gate(1993, rows, picks,
                          {"Penny Hardaway": "Anfernee Hardaway"})
    assert not any("Penny" in p for p in problems)


def test_corrections_fix_typed_fields(tmp_path, monkeypatch):
    corrections = tmp_path / "corrections.csv"
    corrections.write_text(
        "year,team,field,value,note\n"
        "1989,Charlotte,record_w,20,evidence\n"
        "1995,Weird Name *,team,Vancouver,evidence\n")
    monkeypatch.setattr(mod02, "CORRECTIONS", corrections)
    rows = [{"year": 1989, "team": "Charlotte", "record_w": 60},
            {"year": 1995, "team": "Weird Name *", "record_w": 1}]
    mod02.apply_corrections(rows)
    assert rows[0]["record_w"] == 20            # int-typed
    assert rows[1]["team"] == "Vancouver"       # string-typed


def test_corrections_are_optional(tmp_path, monkeypatch):
    monkeypatch.setattr(mod02, "CORRECTIONS", tmp_path / "absent.csv")
    rows = [{"year": 1989, "team": "Charlotte", "record_w": 60}]
    mod02.apply_corrections(rows)
    assert rows[0]["record_w"] == 60


def test_aliases_are_optional(tmp_path, monkeypatch):
    monkeypatch.setattr(mod02, "ALIASES", tmp_path / "absent.csv")
    assert mod02.load_aliases() == {}


def test_lottery_main_is_idempotent_and_gated():
    out = ROOT / "data" / "lottery.csv"
    before = out.read_bytes()
    assert mod02.main() == 0
    assert out.read_bytes() == before


# ── 08: bbref parser against committed pages ────────────────────────────


def test_bbref_parser_reads_career_value_columns():
    rows = mod08.parse_year(2003)
    lebron = rows[0]
    assert (lebron["pick"], lebron["player"]) == (1, "LeBron James")
    assert float(lebron["ws"]) > 250
    assert float(lebron["vorp"]) > 150


def test_bbref_parser_fails_loudly_on_unrecognised_html(tmp_path,
                                                        monkeypatch):
    (tmp_path / "2003.html").write_text("<html><body>nope</body></html>")
    monkeypatch.setattr(mod08, "RAW", tmp_path)
    with pytest.raises(AssertionError):
        mod08.parse_year(2003)


def test_bbref_main_fails_on_unmatched_or_short_years(monkeypatch, capsys):
    fake_stats = {s: "0" for s in mod08.STATS}
    monkeypatch.setattr(
        mod08, "parse_year",
        lambda year: [{"year": year, "pick": 1, "player": "Nobody Real",
                       **fake_stats}])
    assert mod08.main() == 1
    err = capsys.readouterr().err
    assert "picks parsed" in err          # 50-60 row count gate
    assert "matched 0" in err             # unknown name
    assert "no bbref match" in err        # unmatched draft_history picks


def test_bbref_main_matches_every_pick_and_is_idempotent():
    out = ROOT / "data" / "bbref_draft.csv"
    before = out.read_bytes()
    assert mod08.main() == 0
    assert out.read_bytes() == before
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2155


# ── 01 / 03: cache behaviour without the network ────────────────────────


def test_draft_history_harvest_skips_when_cached(tmp_path, monkeypatch,
                                                 capsys):
    (tmp_path / "draft_history.csv").write_text("PERSON_ID\n1\n")
    monkeypatch.setattr(mod01, "DATA", tmp_path)
    assert mod01.main() == 0
    assert "already present" in capsys.readouterr().out


def test_careers_fetch_reports_nothing_to_do_when_cached(tmp_path,
                                                         monkeypatch,
                                                         capsys):
    monkeypatch.setattr(mod03, "CACHE", tmp_path)
    (tmp_path / "7.csv").write_text(",".join(mod03.SEASON_COLS) + "\n")
    assert mod03.fetch_missing([7]) == 0
    assert "0 to fetch" in capsys.readouterr().out


def test_careers_merge_splits_season_and_career_rows(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(mod03, "DATA", tmp_path)
    monkeypatch.setattr(mod03, "CACHE", cache)
    header = ",".join(mod03.SEASON_COLS)
    (cache / "7.csv").write_text(
        f"{header}\n"
        "7,2003-04,1610612739,CLE,19.0,79,79,3120,622,1492,.417,63,217,.29,"
        "347,460,.754,99,333,432,465,130,58,273,149,1654\n"
        "7,CAREER,,,,79,79,3120,622,1492,.417,63,217,.29,"
        "347,460,.754,99,333,432,465,130,58,273,149,1654\n")
    (cache / "8.csv").write_text(header + "\n")  # never played
    mod03.merge([7, 8])
    with (tmp_path / "careers.csv").open() as f:
        seasons = list(csv.DictReader(f))
    with (tmp_path / "career_totals.csv").open() as f:
        totals = list(csv.DictReader(f))
    assert len(seasons) == 1 and seasons[0]["SEASON_ID"] == "2003-04"
    assert len(totals) == 1 and totals[0]["PTS"] == "1654"


def test_careers_main_reports_missing_and_resumes(tmp_path, monkeypatch,
                                                  capsys):
    (tmp_path / "draft_history.csv").write_text("PERSON_ID\n7\n")
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(mod03, "DATA", tmp_path)
    monkeypatch.setattr(mod03, "CACHE", cache)
    monkeypatch.setattr(mod03, "fetch_missing", lambda ids: 1)
    assert mod03.main() == 1
    assert "still uncached" in capsys.readouterr().out
    # Once cached, the same main() merges and succeeds.
    monkeypatch.setattr(mod03, "fetch_missing", lambda ids: 0)
    (cache / "7.csv").write_text(",".join(mod03.SEASON_COLS) + "\n")
    assert mod03.main() == 0


# ── 06: reconcile arithmetic ────────────────────────────────────────────


def _write_pair(tmp_path, name, py_rows, r_rows, header="a,b"):
    (tmp_path / f"{name}.csv").write_text(
        header + "\n" + "\n".join(py_rows) + "\n")
    (tmp_path / f"{name}_r.csv").write_text(
        header + "\n" + "\n".join(r_rows) + "\n")


def test_reconcile_accepts_numeric_agreement_within_tolerance(tmp_path,
                                                              monkeypatch):
    monkeypatch.setattr(mod06, "OUT", tmp_path)
    _write_pair(tmp_path, "t", ["x,1.0000001"], ["x,1.0000002"])
    assert mod06.compare("t") == []


def test_reconcile_rejects_every_kind_of_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(mod06, "OUT", tmp_path)
    _write_pair(tmp_path, "num", ["x,1.0"], ["x,1.1"])
    _write_pair(tmp_path, "text", ["x,1.0"], ["y,1.0"])
    _write_pair(tmp_path, "rows", ["x,1.0", "y,2.0"], ["x,1.0"])
    _write_pair(tmp_path, "head", ["x,1.0"], ["x,1.0"])
    (tmp_path / "head_r.csv").write_text("a,c\nx,1.0\n")
    assert "1.1" in mod06.compare("num")[0]
    assert "'y'" in mod06.compare("text")[0]
    assert "rows" in mod06.compare("rows")[0]
    assert "headers differ" in mod06.compare("head")[0]


def test_reconcile_main_fails_on_disagreement(tmp_path, monkeypatch,
                                              capsys):
    monkeypatch.setattr(mod06, "OUT", tmp_path)
    monkeypatch.setattr(mod06, "TABLES", ["num"])
    _write_pair(tmp_path, "num", ["x,1.0"], ["x,2.0"])
    assert mod06.main() == 1
    assert "RECONCILE FAILURES" in capsys.readouterr().err


def test_reconcile_main_passes_on_the_real_outputs():
    assert mod06.main() == 0


# ── 04: site-data generator ─────────────────────────────────────────────


def test_generator_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(mod04, "OUT", tmp_path)
    assert mod04.main() == 0
    first = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert mod04.main() == 0
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == first
    assert set(first) == {"lottery.js", "drafts.js", "analysis.js"}
    for content in first.values():
        assert content.startswith(b"// GENERATED")


def test_generator_skips_analysis_module_before_the_analysis_runs(
        tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod04, "OUT", tmp_path / "out")
    monkeypatch.setattr(mod04, "ANALYSIS", tmp_path)  # no colleges.csv here
    assert mod04.main() == 0
    assert "skipping analysis.js" in capsys.readouterr().out
    assert not (tmp_path / "out" / "analysis.js").exists()


def test_generated_modules_parse_as_es_modules(tmp_path, monkeypatch):
    monkeypatch.setattr(mod04, "OUT", tmp_path)
    mod04.main()
    for name in ("lottery.js", "drafts.js", "analysis.js"):
        subprocess.run(
            ["node", "--input-type=module", "-e",
             f"await import('{(tmp_path / name).as_posix()}')"],
            check=True)


# ── 07: findings rewriter ───────────────────────────────────────────────


def test_findings_rewrite_is_marker_bounded(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text("intro\n<!-- findings:start -->\nSTALE-SENTINEL\n"
                      "<!-- findings:end -->\noutro\n")
    monkeypatch.setattr(mod07, "README", readme)
    assert mod07.main() == 0
    text = readme.read_text()
    assert text.startswith("intro\n") and text.endswith("outro\n")
    assert "STALE-SENTINEL" not in text
    assert "Win Shares" in text
    # Re-running replaces its own section, not the surroundings.
    assert mod07.main() == 0
    assert readme.read_text() == text


def test_findings_refuse_a_readme_without_markers(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text("no markers here\n")
    monkeypatch.setattr(mod07, "README", readme)
    with pytest.raises(SystemExit):
        mod07.main()


# ── 05: analysis end-to-end determinism ─────────────────────────────────


def test_analysis_is_deterministic():
    mod05 = load_script("05_analyze")
    out = ROOT / "output"
    names = ["pick_curve.csv", "colleges.csv", "teams.csv", "steals.csv"]
    before = {n: (out / n).read_bytes() for n in names}
    assert mod05.main() == 0
    assert {n: (out / n).read_bytes() for n in names} == before


def test_generator_reports_missing_careers(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod04, "DATA", tmp_path)
    assert mod04.load_careers() is None
    monkeypatch.setattr(mod04, "load_careers", lambda: None)
    monkeypatch.setattr(mod04, "load_lottery", lambda: [])
    monkeypatch.setattr(mod04, "load_drafts", lambda careers: [])
    monkeypatch.setattr(mod04, "OUT", tmp_path / "out")
    monkeypatch.setattr(mod04, "ANALYSIS", tmp_path)
    assert mod04.main() == 0
    assert "careers CSVs not present" in capsys.readouterr().out
