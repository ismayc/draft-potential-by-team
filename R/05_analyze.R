# Independent R rebuild of python/05_analyze.py — same questions, same
# definitions, written against the same committed CSVs. The reconcile gate
# (python/06_reconcile.py) compares every number in the four output tables
# to the Python run and fails the build on any disagreement.
#
# Run: Rscript R/05_analyze.R

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(tidyr)
})

root <- normalizePath(file.path(dirname(
  sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
out_dir <- file.path(root, "output")
dir.create(out_dir, showWarnings = FALSE)

window_lo <- 1989
window_hi <- 2015
hit_minutes <- 10000
min_draftees <- 8

bucket_of <- function(pick) {
  case_when(
    pick <= 5 ~ "1-5",
    pick <= 10 ~ "6-10",
    pick <= 14 ~ "11-14",
    pick <= 20 ~ "15-20",
    pick <= 30 ~ "21-30",
    pick <= 45 ~ "31-45",
    TRUE ~ "46-60"
  )
}

totals <- read_csv(file.path(root, "data", "career_totals.csv"),
                   show_col_types = FALSE) |>
  transmute(person_id = as.integer(PLAYER_ID),
            career_min = coalesce(MIN, 0))

draft <- read_csv(file.path(root, "data", "draft_history.csv"),
                  show_col_types = FALSE) |>
  transmute(
    year = SEASON, pick = OVERALL_PICK, player = PLAYER_NAME,
    person_id = PERSON_ID, team_id = TEAM_ID,
    team = trimws(paste(TEAM_CITY, TEAM_NAME)),
    org = ORGANIZATION, org_type = ORGANIZATION_TYPE
  ) |>
  left_join(totals, by = "person_id") |>
  mutate(career_min = coalesce(career_min, 0))

# Current franchise label: city + name on the id's most recent pick.
labels <- draft |>
  arrange(year, pick) |>
  group_by(team_id) |>
  summarise(label = last(team), .groups = "drop")

window <- draft |>
  filter(year >= window_lo, year <= window_hi) |>
  mutate(bucket = bucket_of(pick))

curve <- window |>
  group_by(bucket) |>
  summarise(picks = n(), mean_min = mean(career_min), .groups = "drop")

bucket_order <- c("1-5", "6-10", "11-14", "15-20", "21-30", "31-45", "46-60")
curve |>
  mutate(bucket = factor(bucket, levels = bucket_order)) |>
  arrange(bucket) |>
  mutate(mean_min = round(mean_min, 1)) |>
  write_csv(file.path(out_dir, "pick_curve_r.csv"))

window <- window |>
  left_join(select(curve, bucket, expected = mean_min), by = "bucket") |>
  mutate(value = career_min - expected)

window |>
  filter(org_type == "College/University") |>
  group_by(college = org) |>
  summarise(
    draftees = n(),
    hits = sum(career_min >= hit_minutes),
    hit_rate = round(hits / draftees, 3),
    total_min = round(sum(career_min), 1),
    value_added = round(sum(value), 1),
    .groups = "drop"
  ) |>
  filter(draftees >= min_draftees) |>
  arrange(desc(value_added), college) |>
  write_csv(file.path(out_dir, "colleges_r.csv"))

window |>
  group_by(team_id) |>
  summarise(
    picks = n(),
    avg_pick = round(mean(pick), 1),
    hits = sum(career_min >= hit_minutes),
    total_min = round(sum(career_min), 1),
    expected_min = round(sum(expected), 1),
    value_added = round(sum(value), 1),
    .groups = "drop"
  ) |>
  left_join(labels, by = "team_id") |>
  transmute(team = label, picks, avg_pick, hits,
            total_min, expected_min, value_added) |>
  arrange(desc(value_added), team) |>
  write_csv(file.path(out_dir, "teams_r.csv"))

window |>
  arrange(desc(value), player) |>
  slice_head(n = 15) |>
  left_join(labels, by = "team_id") |>
  transmute(player, year, pick, team = label, college = org,
            career_min = round(career_min, 1),
            expected_min = round(expected, 1),
            value_added = round(value, 1)) |>
  write_csv(file.path(out_dir, "steals_r.csv"))

cat(sprintf("window %d-%d: %d picks\n", window_lo, window_hi, nrow(window)))
for (name in c("pick_curve_r", "colleges_r", "teams_r", "steals_r")) {
  cat(sprintf("wrote output/%s.csv\n", name))
}
