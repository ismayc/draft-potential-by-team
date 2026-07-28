# Pure functions shared by the R analysis and its tests — the R mirror of
# python/draftlib.py. Deterministic, no I/O; unit-tested against the same
# hand-computed fixtures as the Python versions
# (tests/R/test_functions.R / tests/python/test_draftlib.py).

# Weighted isotonic regression, non-increasing in pick (PAVA on the negated
# series) — mirrors draftlib.pava_decreasing().
pava_decreasing <- function(picks, means, weights) {
  vals <- numeric(0); wts <- numeric(0); sizes <- integer(0)
  for (i in seq_along(picks)) {
    vals <- c(vals, -means[i]); wts <- c(wts, weights[i]); sizes <- c(sizes, 1L)
    while (length(vals) > 1 &&
           vals[length(vals) - 1] > vals[length(vals)]) {
      n <- length(vals)
      w <- wts[n - 1] + wts[n]
      vals[n - 1] <- (vals[n - 1] * wts[n - 1] + vals[n] * wts[n]) / w
      wts[n - 1] <- w
      sizes[n - 1] <- sizes[n - 1] + sizes[n]
      vals <- vals[-n]; wts <- wts[-n]; sizes <- sizes[-n]
    }
  }
  -rep(vals, sizes)
}

# Best sum over three consecutive played seasons (chronological order);
# the whole career when it spans three seasons or fewer — mirrors
# draftlib.peak3().
peak3_seasons <- function(effs) {
  if (length(effs) == 0) return(0)
  if (length(effs) <= 3) return(sum(effs))
  max(vapply(seq_len(length(effs) - 2),
             \(i) sum(effs[i:(i + 2)]), numeric(1)))
}
