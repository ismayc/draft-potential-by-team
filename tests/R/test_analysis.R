# Invariants of the R analysis outputs (output/*_r.csv).
suppressPackageStartupMessages({
  library(testthat)
  library(readr)
})

out <- file.path(root, "output")

test_that("WS value is zero-sum across the 30 franchises", {
  teams <- read_csv(file.path(out, "teams_r.csv"), show_col_types = FALSE)
  expect_lt(abs(sum(teams$value_ws)), 5)
  expect_equal(nrow(teams), 30)
})

test_that("every pick curve declines monotonically", {
  curve <- read_csv(file.path(out, "pick_curve_r.csv"), show_col_types = FALSE)
  expect_equal(nrow(curve), 60)
  for (col in c("exp_ws", "exp_min", "exp_vorp", "exp_peak3")) {
    expect_true(all(diff(curve[[col]]) <= 0), info = col)
  }
})

test_that("confidence intervals bracket the estimate", {
  teams <- read_csv(file.path(out, "teams_r.csv"), show_col_types = FALSE)
  expect_true(all(teams$ci_lo <= teams$value_ws & teams$value_ws <= teams$ci_hi))
})

test_that("kept minutes are a valid share", {
  teams <- read_csv(file.path(out, "teams_r.csv"), show_col_types = FALSE)
  expect_true(all(teams$kept_share >= 0 & teams$kept_share <= 1))
  expect_true(all(teams$kept_min >= 0))
})

test_that("college hit rates are consistent", {
  colleges <- read_csv(file.path(out, "colleges_r.csv"), show_col_types = FALSE)
  expect_true(all(colleges$hits >= 0 & colleges$hits <= colleges$draftees))
  expect_true(all(colleges$draftees >= 8))
  expect_equal(colleges$hit_rate, round(colleges$hits / colleges$draftees, 3))
})

test_that("steals are positive and ranked", {
  steals <- read_csv(file.path(out, "steals_r.csv"), show_col_types = FALSE)
  expect_equal(nrow(steals), 15)
  expect_true(all(steals$value_ws > 0))
  expect_equal(steals$value_ws, sort(steals$value_ws, decreasing = TRUE))
})
