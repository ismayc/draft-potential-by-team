# Independent R rebuild of python/05_analyze.py (v2) — same questions, same
# definitions: career Win Shares as the headline outcome, weighted isotonic
# (non-increasing) slot expectations over picks 1..60, drafting-franchise
# minutes split, peak-3-consecutive-season efficiency, normal-approximation
# CIs, within-class z values. python/06_reconcile.py holds the two equal.
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

source(file.path(dirname(
  sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))),
  "functions.R"))

totals <- read_csv(file.path(root, "data", "career_totals.csv"),
                   show_col_types = FALSE) |>
  transmute(person_id = as.integer(PLAYER_ID),
            career_min = coalesce(MIN, 0))

bbref <- read_csv(file.path(root, "data", "bbref_draft.csv"),
                  show_col_types = FALSE) |>
  transmute(year, pick, ws = coalesce(ws, 0), vorp = coalesce(vorp, 0))

seasons <- read_csv(file.path(root, "data", "careers.csv"),
                    show_col_types = FALSE) |>
  mutate(across(c(PTS, REB, AST, STL, BLK, FGA, FGM, FTA, FTM, TOV, MIN),
                \(x) coalesce(x, 0)),
         eff = PTS + REB + AST + STL + BLK - (FGA - FGM) - (FTA - FTM) - TOV)

# Per-season efficiency: a multi-team season keeps its TOT row, otherwise
# the team rows sum to the season.
season_eff <- seasons |>
  group_by(person_id = PLAYER_ID, season = SEASON_ID) |>
  summarise(
    eff = if (any(TEAM_ABBREVIATION == "TOT", na.rm = TRUE)) {
      sum(eff[TEAM_ABBREVIATION == "TOT"])
    } else {
      sum(eff)
    },
    .groups = "drop"
  )

peak3 <- season_eff |>
  arrange(person_id, season) |>
  group_by(person_id) |>
  summarise(peak3 = peak3_seasons(eff), .groups = "drop")

franchise_min <- seasons |>
  filter(TEAM_ABBREVIATION != "TOT" | is.na(TEAM_ABBREVIATION)) |>
  group_by(person_id = PLAYER_ID, team_id = as.integer(TEAM_ID)) |>
  summarise(fmin = sum(MIN), .groups = "drop")

draft <- read_csv(file.path(root, "data", "draft_history.csv"),
                  show_col_types = FALSE) |>
  transmute(
    year = SEASON, pick = OVERALL_PICK, player = PLAYER_NAME,
    person_id = PERSON_ID, team_id = TEAM_ID,
    team = trimws(paste(TEAM_CITY, TEAM_NAME)),
    org = ORGANIZATION, org_type = ORGANIZATION_TYPE
  ) |>
  left_join(totals, by = "person_id") |>
  left_join(bbref, by = c("year", "pick")) |>
  left_join(peak3, by = "person_id") |>
  left_join(franchise_min, by = c("person_id", "team_id")) |>
  mutate(min = coalesce(career_min, 0),
         ws = coalesce(ws, 0), vorp = coalesce(vorp, 0),
         peak3 = coalesce(peak3, 0), kept_min = coalesce(fmin, 0))

labels <- draft |>
  arrange(year, pick) |>
  group_by(team_id) |>
  summarise(label = last(team), .groups = "drop")

window <- draft |> filter(year >= window_lo, year <= window_hi)

# ── Slot expectations ────────────────────────────────────────────────────
per_pick <- window |>
  group_by(pick) |>
  summarise(picks = n(), m_ws = mean(ws), m_min = mean(min),
            m_vorp = mean(vorp), m_peak3 = mean(peak3), .groups = "drop") |>
  arrange(pick)

curve <- per_pick |>
  mutate(
    exp_ws = pava_decreasing(pick, m_ws, picks),
    exp_min = pava_decreasing(pick, m_min, picks),
    exp_vorp = pava_decreasing(pick, m_vorp, picks),
    exp_peak3 = pava_decreasing(pick, m_peak3, picks)
  )

curve |>
  transmute(pick, picks, exp_ws = round(exp_ws, 3),
            exp_min = round(exp_min, 3), exp_vorp = round(exp_vorp, 3),
            exp_peak3 = round(exp_peak3, 3)) |>
  write_csv(file.path(out_dir, "pick_curve_r.csv"))

window <- window |>
  left_join(select(curve, pick, exp_ws, exp_min, exp_vorp, exp_peak3),
            by = "pick") |>
  mutate(v_ws = ws - exp_ws, v_min = min - exp_min,
         v_vorp = vorp - exp_vorp, v_peak3 = peak3 - exp_peak3) |>
  group_by(year) |>
  mutate(v_ws_z = v_ws / sd(v_ws)) |>
  ungroup()

# ── Colleges ─────────────────────────────────────────────────────────────
window |>
  filter(org_type == "College/University") |>
  group_by(college = org) |>
  summarise(
    draftees = n(),
    hits = sum(min >= hit_minutes),
    hit_rate = round(hits / draftees, 3),
    total_ws = round(sum(ws), 1),
    value_ws = round(sum(v_ws), 1),
    value_ws_z = round(sum(v_ws_z), 2),
    value_vorp = round(sum(v_vorp), 1),
    value_min = round(sum(v_min), 1),
    .groups = "drop"
  ) |>
  filter(draftees >= min_draftees) |>
  arrange(desc(value_ws), college) |>
  write_csv(file.path(out_dir, "colleges_r.csv"))

# ── Teams ────────────────────────────────────────────────────────────────
window |>
  group_by(team_id) |>
  summarise(
    picks = n(),
    avg_pick = round(mean(pick), 1),
    hits = sum(min >= hit_minutes),
    total_ws = round(sum(ws), 1),
    raw_value = sum(v_ws),
    half = 1.96 * sd(v_ws) * sqrt(n()),
    value_ws = round(raw_value, 1),
    ci_lo = round(raw_value - half, 1),
    ci_hi = round(raw_value + half, 1),
    value_ws_z = round(sum(v_ws_z), 2),
    value_vorp = round(sum(v_vorp), 1),
    value_min = round(sum(v_min), 1),
    kept_min = round(sum(kept_min), 1),
    kept_share = round(sum(kept_min) / sum(min), 3),
    .groups = "drop"
  ) |>
  left_join(labels, by = "team_id") |>
  transmute(team = label, picks, avg_pick, hits, total_ws, value_ws,
            ci_lo, ci_hi, value_ws_z, value_vorp, value_min,
            kept_min, kept_share) |>
  arrange(desc(value_ws), team) |>
  write_csv(file.path(out_dir, "teams_r.csv"))

# ── Steals ───────────────────────────────────────────────────────────────
window |>
  arrange(desc(v_ws), player) |>
  slice_head(n = 15) |>
  left_join(labels, by = "team_id") |>
  transmute(player, year, pick, team = label, college = org,
            ws = round(ws, 1), expected_ws = round(exp_ws, 1),
            value_ws = round(v_ws, 1), vorp = round(vorp, 1)) |>
  write_csv(file.path(out_dir, "steals_r.csv"))

cat(sprintf("window %d-%d: %d picks\n", window_lo, window_hi, nrow(window)))
for (name in c("pick_curve_r", "colleges_r", "teams_r", "steals_r")) {
  cat(sprintf("wrote output/%s.csv\n", name))
}
