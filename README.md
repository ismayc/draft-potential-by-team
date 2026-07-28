# NBA Draft Potential by Team

[![CI](https://github.com/ismayc/draft-potential-by-team/actions/workflows/ci.yml/badge.svg)](https://github.com/ismayc/draft-potential-by-team/actions/workflows/ci.yml)
[![coverage](https://img.shields.io/endpoint?url=https%3A%2F%2Fismayc.github.io%2Fdraft-potential-by-team%2Fcoverage.json)](https://github.com/ismayc/draft-potential-by-team/actions/workflows/ci.yml)

An unofficial viewer for every NBA draft of the two-round era (1989–present):
the lottery as it actually unfolded — pre-lottery odds, the order the drawing
produced, who jumped and who fell — and the full two-round draft board with
what each pick became over an NBA career.

**Live site: <https://ismayc.github.io/draft-potential-by-team/>**

## Views

- **Lottery** — each year's lottery teams with their record, odds, chances,
  the resulting pick order, movement up or down from the inverse-record seed,
  and the player selected at that slot.
- **Draft board** — both rounds of each draft: player, drafting team, college
  or origin, and career totals (games, minutes, points, seasons, franchises).
- **Colleges** — every program with 8+ draftees ranked by career Win Shares
  its picks delivered above slot expectation (from the reconciled analysis).
- **Teams** — all 30 franchises ranked the same way with 95% intervals and
  the share of drafted careers each kept, plus the biggest individual steals.
- **About** — provenance, how the lottery formats changed, and caveats.

Navigation follows the URL: `?view=draft&year=1993` is shareable state.

## Findings

<!-- findings:start -->

Draft classes 1989-2015 (every class with ten full NBA seasons to
accumulate a career). The headline outcome is career Win Shares
(Basketball-Reference); value is WS above the expectation for the
pick slot, where the expectation curve is a weighted isotonic fit
over picks 1-60 — no buckets, no functional form.

- The slot gradient: pick 1 carries an expectation of
  77 career Win Shares; pick 60 carries 2.

**Colleges producing the most NBA value** (8+ draftees; hits are
careers of 10,000+ minutes):

| College | Draftees | Hits | Hit rate | WS above slot |
| --- | --- | --- | --- | --- |
| Wake Forest | 10 | 7 | 70% | +323 |
| California-Los Angeles | 36 | 16 | 44% | +224 |
| Marquette | 11 | 3 | 27% | +201 |
| Florida | 18 | 10 | 56% | +142 |
| Xavier | 11 | 4 | 36% | +117 |

Among colleges with 15+ draftees, Kentucky has the
best hit rate: 25 of 41
picks (61%) became 10,000-minute
NBA players.

**Teams drafting the best, relative to where they picked** (the
95% interval is a normal approximation on the team's pick values;
kept share is the fraction of drafted careers' minutes played for
the drafting franchise):

| Franchise | Picks | Avg pick | WS above slot | 95% interval | Kept share |
| --- | --- | --- | --- | --- | --- |
| Oklahoma City Thunder | 69 | 31.1 | +489 | -14 to 992 | 38% |
| San Antonio Spurs | 50 | 40.8 | +411 | -10 to 832 | 44% |
| Los Angeles Lakers | 48 | 35.8 | +251 | -76 to 578 | 41% |
| Phoenix Suns | 60 | 34.1 | +240 | -164 to 644 | 33% |
| Golden State Warriors | 56 | 27.2 | +204 | -187 to 595 | 46% |

The LA Clippers sit last (-394 WS against
slot expectation). Draft value is heavy-tailed: 27 of 30
franchise intervals cross zero, so most of the league is
statistically indistinguishable on drafting skill — the ordering
is the estimate, not a verdict. The
Golden State Warriors kept the largest share of the careers they
drafted (46% of minutes).

**The biggest steals** (career WS furthest above the pick's slot
expectation):

| Player | Year | Pick | Drafted by | WS above slot |
| --- | --- | --- | --- | --- |
| LeBron James | 2003 | 1 | Cleveland Cavaliers | +200 |
| Dirk Nowitzki | 1998 | 9 | Milwaukee Bucks | +170 |
| Chris Paul | 2005 | 4 | New Orleans Pelicans | +155 |
| Kobe Bryant | 1996 | 13 | Charlotte Hornets | +145 |
| Kevin Garnett | 1995 | 5 | Minnesota Timberwolves | +136 |

Full tables: `output/colleges.csv`, `output/teams.csv`,
`output/steals.csv`, `output/pick_curve.csv` — each with VORP,
career-minutes, and within-class-z companion columns, and each
mirrored by an `_r.csv` twin from the independent R implementation
(the reconcile gate holds them equal).

<!-- findings:end -->

## Data pipeline

Python scripts in `python/`, run in order, all idempotent (a re-run touches
nothing already fetched):

| Script | Source | Output |
| --- | --- | --- |
| `01_harvest_draft_history.py` | NBA Stats `DraftHistory` via [nba_api](https://github.com/swar/nba_api) | `data/draft_history.csv` (2,155 picks, 1989–2025) |
| `02_harvest_lottery.py` | [The Draft Review](https://www.thedraftreview.com) lottery pages (cached raw in `data/raw/lottery/`) | `data/lottery.csv` (489 team-lottery rows) |
| `03_harvest_careers.py` | NBA Stats `PlayerCareerStats`, one call per drafted player, resumable | `data/careers.csv`, `data/career_totals.csv` |
| `04_generate_site_data.py` | the CSVs above + `output/` tables | `src/data/lottery.js`, `src/data/drafts.js`, `src/data/analysis.js` |
| `08_harvest_bbref.py` | [Basketball-Reference](https://www.basketball-reference.com) draft pages (cached raw in `data/raw/bbref/`) | `data/bbref_draft.csv` (career WS, WS/48, BPM, VORP per pick) |
| `05_analyze.py` | the CSVs above | `output/{pick_curve,colleges,teams,steals}.csv` |
| `06_reconcile.py` | `output/*.csv` vs `output/*_r.csv` | non-zero exit on any Python/R disagreement |
| `07_findings.py` | `output/*.csv` | the Findings section of this README |

`R/05_analyze.R` is an independent tidyverse rebuild of `05_analyze.py`
writing `output/*_r.csv`; the reconcile gate holds the two implementations
equal, so a finding only exists once both languages produce it.

## Testing

Correctness is enforced at four layers, all run by `./run_checks.sh` and CI:

- **Site** — vitest at 100% statement/branch/function/line coverage,
  asserting known ground truth against the real data modules.
- **Python pipeline** — pytest at 100% statement coverage
  (`.coveragerc`; network I/O is pragma-excluded and exercised by the real
  harvest runs instead). Pure functions (`python/draftlib.py`: the isotonic
  fit, name normalisation, peak-3 window, sample sd) are unit-tested
  against hand-computed fixtures; parsers are tested against the committed
  raw HTML; every gate's failure path is triggered deliberately.
- **R** — testthat runs the same hand-computed fixtures against
  `R/functions.R` plus invariant checks on the outputs, pinning both
  implementations to the same expected numbers, not just to each other.
- **Cross-language** — `06_reconcile.py` requires every cell of every
  output table to agree between Python and R within 1e-6.

The CSVs are the source of truth — analysis (Python and R) reads them
directly; the JS modules are a derived re-expression so the site renders with
zero runtime network requests.

`02_harvest_lottery.py` gates every parsed year: expected team count for the
era, odds summing to ~100%, contiguous result positions, seeds within range,
and the player at every lottery slot cross-checked against `draft_history.csv`
(name variants audited by hand into `data/manual/aliases.csv`).

```sh
uv venv .venv && uv pip install -r requirements.txt --python .venv/bin/python
.venv/bin/python python/01_harvest_draft_history.py
.venv/bin/python python/02_harvest_lottery.py
.venv/bin/python python/03_harvest_careers.py   # ~1 hour first run, resumable
.venv/bin/python python/08_harvest_bbref.py
.venv/bin/python python/05_analyze.py && Rscript R/05_analyze.R
.venv/bin/python python/06_reconcile.py && .venv/bin/python python/07_findings.py
.venv/bin/python python/04_generate_site_data.py
```

## Site

React 18 + Vite, no router, no state library, no runtime requests. Committed
data modules render instantly; two query parameters (`view`, `year`) carry all
shareable state.

```sh
npm install
npm run dev            # local dev server
npm run test:coverage  # vitest, held at 100% coverage
npm run build          # production build in dist/
```

CI tests, builds, and deploys to GitHub Pages on every push to `main`.

## Provenance and caveats

- Lottery odds, chances, and results are parsed from The Draft Review's
  per-year lottery pages, fetched once and committed under `data/raw/` for
  reproducibility. Odds are stored as printed, never recomputed — including
  the unweighted 1989 lottery and coin-flip-tied seeds.
- Draft picks, colleges, and career statistics come from NBA Stats via
  nba_api. Career totals are regular season only.
- Forfeited picks are absent, so some drafts have fewer than 60 selections.
- The lottery table shows the team that held the pick on lottery night; picks
  are often traded before and after the drawing.
- Draft value is credited to the franchise that made the selection, so
  draft-night trades land on the selecting team (Dirk Nowitzki counts for
  Milwaukee, not Dallas; Kobe Bryant for Charlotte, not the Lakers). The
  kept-share column separates that scouting credit from retention.
- Win Shares is an estimate of wins contributed, not ground truth; VORP,
  career minutes, peak-3-season efficiency, and within-class z values ride
  alongside in `output/` as robustness companions. Most franchise 95%
  intervals cross zero — the rankings are estimates with real uncertainty.

Unofficial; not affiliated with the NBA.
