# Fixture tests for R/functions.R — the same hand-computed expectations as
# tests/python/test_draftlib.py, so both implementations are pinned to the
# same numbers, not just to each other.
suppressPackageStartupMessages(library(testthat))

source(file.path(root, "R", "functions.R"))

test_that("PAVA pools adjacent violators", {
  fit <- pava_decreasing(c(1, 2, 3, 4), c(10, 12, 5, 6), c(1, 1, 1, 1))
  expect_equal(fit, c(11, 11, 5.5, 5.5))
})

test_that("PAVA weights shift the pooled mean", {
  expect_equal(pava_decreasing(c(1, 2), c(4, 8), c(3, 1)), c(5, 5))
})

test_that("PAVA leaves already-decreasing input untouched", {
  expect_equal(pava_decreasing(c(1, 2, 3), c(9, 7, 3), c(1, 1, 1)),
               c(9, 7, 3))
})

test_that("PAVA handles a single point", {
  expect_equal(pava_decreasing(7, 5, 2), 5)
})

test_that("PAVA cascades merges across blocks", {
  expect_equal(pava_decreasing(c(1, 2, 3), c(1, 2, 9), c(1, 1, 1)),
               c(4, 4, 4))
})

test_that("PAVA output is always non-increasing", {
  means <- (seq(1, 7) * 7) %% 5
  fit <- pava_decreasing(1:7, means, 1:7)
  expect_true(all(diff(fit) <= 0))
})

test_that("peak3 handles empty and short careers", {
  expect_equal(peak3_seasons(numeric(0)), 0)
  expect_equal(peak3_seasons(4), 4)
  expect_equal(peak3_seasons(c(1, 2)), 3)
  expect_equal(peak3_seasons(c(1, 2, 3)), 6)
})

test_that("peak3 picks the best consecutive window", {
  expect_equal(peak3_seasons(c(1, 10, 1, 8, 9)), 19)
})

test_that("peak3 picks the least-bad window of a negative career", {
  expect_equal(peak3_seasons(c(-5, -1, -2, -3)), -6)
})
