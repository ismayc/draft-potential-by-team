# Invariants of the R analysis outputs (output/*_r.csv).
suppressPackageStartupMessages({
  library(testthat)
  library(readr)
})

out <- file.path(root, "output")

test_that("value added is zero-sum across the 30 franchises", {
  teams <- read_csv(file.path(out, "teams_r.csv"), show_col_types = FALSE)
  expect_lt(abs(sum(teams$value_added)), 5)
  expect_equal(nrow(teams), 30)
})

test_that("the pick curve declines monotonically", {
  curve <- read_csv(file.path(out, "pick_curve_r.csv"), show_col_types = FALSE)
  expect_equal(curve$mean_min, sort(curve$mean_min, decreasing = TRUE))
  expect_equal(nrow(curve), 7)
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
  expect_true(all(steals$value_added > 0))
  expect_equal(steals$value_added, sort(steals$value_added, decreasing = TRUE))
})
