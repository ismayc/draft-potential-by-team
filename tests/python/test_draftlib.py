"""Fixture tests for the pure functions in python/draftlib.py.

The PAVA and peak3 fixtures are hand-computed and repeated verbatim in
tests/R/test_functions.R, so the two implementations are pinned to the
same expected numbers, not just to each other.
"""
import math

import pytest

from draftlib import norm, pava_decreasing, peak3, sample_sd


class TestPavaDecreasing:
    def test_pools_adjacent_violators(self):
        # Hand-computed: (10, 12) violate -> pool to 11; (5, 6) -> 5.5.
        fit = pava_decreasing([1, 2, 3, 4],
                              {1: 10.0, 2: 12.0, 3: 5.0, 4: 6.0},
                              {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0})
        assert fit == {1: 11.0, 2: 11.0, 3: 5.5, 4: 5.5}

    def test_weights_shift_the_pooled_mean(self):
        # (4*3 + 8*1) / 4 = 5 — the heavier early pick dominates the pool.
        fit = pava_decreasing([1, 2], {1: 4.0, 2: 8.0}, {1: 3.0, 2: 1.0})
        assert fit == {1: 5.0, 2: 5.0}

    def test_already_decreasing_input_is_untouched(self):
        fit = pava_decreasing([1, 2, 3], {1: 9.0, 2: 7.0, 3: 3.0},
                              {1: 1.0, 2: 1.0, 3: 1.0})
        assert fit == {1: 9.0, 2: 7.0, 3: 3.0}

    def test_single_point(self):
        assert pava_decreasing([7], {7: 5.0}, {7: 2.0}) == {7: 5.0}

    def test_cascading_merge_spans_blocks(self):
        # A late high value must pool backwards through multiple blocks.
        fit = pava_decreasing([1, 2, 3], {1: 1.0, 2: 2.0, 3: 9.0},
                              {1: 1.0, 2: 1.0, 3: 1.0})
        assert fit == {1: 4.0, 2: 4.0, 3: 4.0}

    def test_output_is_always_non_increasing(self):
        fit = pava_decreasing(list(range(1, 8)),
                              {p: float((p * 7) % 5) for p in range(1, 8)},
                              {p: float(p) for p in range(1, 8)})
        vals = [fit[p] for p in range(1, 8)]
        assert all(a >= b for a, b in zip(vals, vals[1:]))


class TestNorm:
    @pytest.mark.parametrize("raw,expected", [
        ("Luka Dončić", "lukadoncic"),          # diacritics
        ("Tibor Pleiß", "tiborpleiss"),         # sharp-s via casefold
        ("Ömer Aşık", "omerasik"),              # Turkish dotless i
        ("J.R. Rider", "jrrider"),              # leading initials keep jr
        ("Jaren Jackson, Jr.", "jarenjackson"),  # comma suffix
        ("Ronald Holland II", "ronaldholland"),  # roman-numeral suffix
        ("Clar. Weatherspoon", "clarweatherspoon"),
    ])
    def test_edge_case_names(self, raw, expected):
        assert norm(raw) == expected

    def test_cross_source_variants_collide(self):
        assert norm("Wang Zhi-zhi") == norm("Wang Zhizhi")
        assert norm("Michael Porter, Jr.") == norm("Michael Porter Jr.")
        assert norm("Nikola Topić") == norm("Nikola Topic")

    def test_distinct_players_stay_distinct(self):
        assert norm("Jaren Jackson") != norm("Jarrett Jack")

    def test_suffix_collision_is_by_design(self):
        # Suffixes are stripped, so a Jr. collides with the father — the
        # join scope is always a single draft year, where that cannot
        # happen.
        assert norm("Tim Hardaway") == norm("Tim Hardaway Jr.")

    def test_idempotent(self):
        for raw in ("Luka Dončić", "J.R. Rider", "Wang Zhi-zhi"):
            assert norm(norm(raw)) == norm(raw)


class TestSampleSd:
    def test_degenerate_inputs_are_zero(self):
        assert sample_sd([]) == 0.0
        assert sample_sd([5.0]) == 0.0

    def test_matches_n_minus_one_definition(self):
        assert sample_sd([1.0, 3.0]) == pytest.approx(math.sqrt(2))
        assert sample_sd([1.0, 2.0, 3.0, 4.0]) == pytest.approx(
            math.sqrt(5.0 / 3.0))


class TestPeak3:
    def test_empty_career_is_zero(self):
        assert peak3([]) == 0.0

    def test_short_careers_sum_everything(self):
        assert peak3([4.0]) == 4.0
        assert peak3([1.0, 2.0]) == 3.0
        assert peak3([1.0, 2.0, 3.0]) == 6.0

    def test_picks_best_consecutive_window(self):
        # Windows: 12, 19, 18 — the middle window wins.
        assert peak3([1.0, 10.0, 1.0, 8.0, 9.0]) == 19.0

    def test_all_negative_seasons_pick_least_bad_window(self):
        assert peak3([-5.0, -1.0, -2.0, -3.0]) == -6.0
