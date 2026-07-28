# Run the R test files with testthat. Non-zero exit on any failure.
suppressPackageStartupMessages(library(testthat))

args <- commandArgs(FALSE)
root <- normalizePath(file.path(dirname(
  sub("--file=", "", grep("--file=", args, value = TRUE))), "..", ".."))

results <- test_dir(file.path(root, "tests", "R"),
                    env = list2env(list(root = root)),
                    stop_on_failure = TRUE)
