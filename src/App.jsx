import { useEffect, useMemo, useState } from 'react'
import LotteryView from './components/LotteryView.jsx'
import DraftBoardView from './components/DraftBoardView.jsx'
import CollegesView from './components/CollegesView.jsx'
import TeamsView from './components/TeamsView.jsx'
import AboutView from './components/AboutView.jsx'
import { DRAFT_YEARS } from './data/drafts.js'
import { readState, writeState } from './utils/urlState.js'

/**
 * The shell: everything is a pure function of two choices — which view and
 * which draft year. Both live in useState and serialise into the query
 * string; there is no router, no state library, and no network request.
 */

const VIEWS = [
  { id: 'lottery', label: 'Lottery' },
  { id: 'draft', label: 'Draft board' },
  { id: 'colleges', label: 'Colleges' },
  { id: 'teams', label: 'Teams' },
  { id: 'about', label: 'About' },
]

// Only the per-year views use the year picker; the analysis views aggregate
// a fixed window and About is prose.
const YEAR_VIEWS = ['lottery', 'draft']

export default function App() {
  const initial = useMemo(() => readState(), [])

  const [view, setView] = useState(initial.view)
  const [year, setYear] = useState(initial.year)
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'dark')

  // Newest first, and a shared or stale link with a year outside the data
  // falls back to the newest draft rather than a blank page.
  const years = useMemo(() => [...DRAFT_YEARS].sort((a, b) => b - a), [])
  const active = years.includes(year) ? year : years[0]

  useEffect(() => {
    writeState({ view, year })
  }, [view, year])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      localStorage.setItem('dpt:theme', theme)
    } catch {
      // Private mode; the theme still applies for this session.
    }
  }, [theme])

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>NBA Draft</h1>
          <span className="era">two-round era, 1989–{years[0]}</span>
        </div>

        <div className="topbar-tools">
          {YEAR_VIEWS.includes(view) && (
            <label className="year-pick">
              <span className="sr-only">Draft year</span>
              <select value={active} onChange={(e) => setYear(Number(e.target.value))}>
                {years.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </label>
          )}

          <button
            type="button"
            className="chip"
            onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            {theme === 'dark' ? '☀' : '☾'}
          </button>
        </div>
      </header>

      <nav className="views" aria-label="Views">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            type="button"
            className={`view-btn ${view === v.id ? 'active' : ''}`}
            onClick={() => setView(v.id)}
            aria-current={view === v.id ? 'page' : undefined}
          >
            {v.label}
          </button>
        ))}
      </nav>

      {view === 'lottery' && <LotteryView year={active} />}
      {view === 'draft' && <DraftBoardView year={active} />}
      {view === 'colleges' && <CollegesView />}
      {view === 'teams' && <TeamsView />}
      {view === 'about' && <AboutView />}

      <footer className="foot">
        <p>
          Unofficial. Lottery odds and results from{' '}
          <a href="https://www.thedraftreview.com" rel="noreferrer noopener" target="_blank">
            The Draft Review
          </a>
          ; draft picks and career statistics from NBA Stats via{' '}
          <a href="https://github.com/swar/nba_api" rel="noreferrer noopener" target="_blank">
            nba_api
          </a>
          . Not affiliated with the NBA.
        </p>
      </footer>
    </div>
  )
}
