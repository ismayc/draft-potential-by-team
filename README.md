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
- **Colleges** — every program with 8+ draftees ranked by career minutes
  its picks delivered above slot expectation (from the reconciled analysis).
- **Teams** — all 30 franchises ranked the same way, plus the biggest
  individual steals.
- **About** — provenance, how the lottery formats changed, and caveats.

Navigation follows the URL: `?view=draft&year=1993` is shareable state.

## Findings

<!-- findings:start -->

Draft classes 1989-2015 (every class with ten full NBA seasons to
accumulate a career), value measured in career regular-season
minutes relative to the mean for the pick's slot bucket.

- The slot gradient is steep: picks 1-5 average
  23,803 career minutes; picks 46-60 average 2,133
  (11x).

**Colleges producing the most NBA talent** (8+ draftees; hits are
careers of 10,000+ minutes):

| College | Draftees | Hits | Hit rate | Minutes above slot |
| --- | --- | --- | --- | --- |
| California-Los Angeles | 36 | 16 | 44% | +121,156 |
| North Carolina | 33 | 18 | 55% | +67,901 |
| Wake Forest | 10 | 7 | 70% | +67,849 |
| Alabama | 13 | 5 | 38% | +59,480 |
| Marquette | 11 | 3 | 27% | +44,280 |

Among colleges with 15+ draftees, Kentucky has the
best hit rate: 25 of 41
picks (61%) became 10,000-minute
NBA players.

**Teams drafting the best, relative to where they picked**:

| Franchise | Picks | Avg pick | Hits | Minutes above slot |
| --- | --- | --- | --- | --- |
| Oklahoma City Thunder | 69 | 31.1 | 25 | +128,901 |
| Los Angeles Lakers | 48 | 35.8 | 15 | +97,750 |
| San Antonio Spurs | 50 | 40.8 | 16 | +96,198 |
| Cleveland Cavaliers | 50 | 26.2 | 22 | +70,758 |
| Phoenix Suns | 60 | 34.1 | 18 | +68,283 |

At the other end, the Dallas Mavericks sit last: -117,355 minutes against slot expectation across 54 picks.

**The biggest steals** (career minutes furthest above the pick's
slot mean):

| Player | Year | Pick | Drafted by | Minutes above slot |
| --- | --- | --- | --- | --- |
| Clifford Robinson | 1989 | 36 | Portland Trail Blazers | +37,908 |
| LeBron James | 2003 | 1 | Cleveland Cavaliers | +37,225 |
| Kobe Bryant | 1996 | 13 | Charlotte Hornets | +36,301 |
| Dirk Nowitzki | 1998 | 9 | Milwaukee Bucks | +34,101 |
| Tony Parker | 2001 | 28 | San Antonio Spurs | +29,392 |

Full tables: `output/colleges.csv`, `output/teams.csv`,
`output/steals.csv`, `output/pick_curve.csv` (each mirrored by an
`_r.csv` twin from the independent R implementation; the reconcile
gate holds them equal).

<!-- findings:end -->

## Data pipeline

Python scripts in `python/`, run in order, all idempotent (a re-run touches
nothing already fetched):

| Script | Source | Output |
| --- | --- | --- |
| `01_harvest_draft_history.py` | NBA Stats `DraftHistory` via [nba_api](https://github.com/swar/nba_api) | `data/draft_history.csv` (2,155 picks, 1989–2025) |
| `02_harvest_lottery.py` | [The Draft Review](https://www.thedraftreview.com) lottery pages (cached raw in `data/raw/lottery/`) | `data/lottery.csv` (489 team-lottery rows) |
| `03_harvest_careers.py` | NBA Stats `PlayerCareerStats`, one call per drafted player, resumable | `data/careers.csv`, `data/career_totals.csv` |
| `04_generate_site_data.py` | the CSVs above | `src/data/lottery.js`, `src/data/drafts.js` |
| `05_analyze.py` | the CSVs above | `output/{pick_curve,colleges,teams,steals}.csv` |
| `06_reconcile.py` | `output/*.csv` vs `output/*_r.csv` | non-zero exit on any Python/R disagreement |
| `07_findings.py` | `output/*.csv` | the Findings section of this README |

`R/05_analyze.R` is an independent tidyverse rebuild of `05_analyze.py`
writing `output/*_r.csv`; the reconcile gate holds the two implementations
equal, so a finding only exists once both languages produce it.
`./run_checks.sh` runs everything: site tests, pytest, testthat, reconcile.

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
  Milwaukee, not Dallas; Kobe Bryant for Charlotte, not the Lakers). Career
  minutes measure longevity and trust, not peak stardom, and take no account
  of where the minutes were played.

Unofficial; not affiliated with the NBA.
