#!/usr/bin/env bash
# The full gate: site tests at 100% coverage, Python analysis invariants,
# R analysis invariants, and the Python-vs-R reconcile. Non-zero exit on
# any failure.
set -euo pipefail
cd "$(dirname "$0")"

PY=${PY:-.venv/bin/python}

echo "── site tests (vitest, 100% coverage) ──"
npm run test:coverage

echo "── python analysis tests (pytest) ──"
"$PY" -m pytest tests/python -q

echo "── R analysis tests (testthat) ──"
Rscript tests/R/run_tests.R

echo "── reconcile Python vs R ──"
"$PY" python/06_reconcile.py

echo "ALL CHECKS PASSED"
