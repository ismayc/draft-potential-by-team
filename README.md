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
- **About** — provenance, how the lottery formats changed, and caveats.

Navigation follows the URL: `?view=draft&year=1993` is shareable state.

## Data pipeline

Python scripts in `python/`, run in order, all idempotent (a re-run touches
nothing already fetched):

| Script | Source | Output |
| --- | --- | --- |
| `01_harvest_draft_history.py` | NBA Stats `DraftHistory` via [nba_api](https://github.com/swar/nba_api) | `data/draft_history.csv` (2,155 picks, 1989–2025) |
| `02_harvest_lottery.py` | [The Draft Review](https://www.thedraftreview.com) lottery pages (cached raw in `data/raw/lottery/`) | `data/lottery.csv` (489 team-lottery rows) |
| `03_harvest_careers.py` | NBA Stats `PlayerCareerStats`, one call per drafted player, resumable | `data/careers.csv`, `data/career_totals.csv` |
| `04_generate_site_data.py` | the CSVs above | `src/data/lottery.js`, `src/data/drafts.js` |

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

Unofficial; not affiliated with the NBA.
