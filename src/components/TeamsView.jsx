import { STEALS, TEAMS, WINDOW } from '../data/analysis.js'

/**
 * Which franchises have drafted best — all 30, ranked by career minutes
 * their picks delivered above the expectation for where they were taken —
 * plus the individual picks that beat their slot by the most. Value is
 * credited to the selecting franchise, draft-night trades included.
 */

function fmt(n) {
  return Math.round(n).toLocaleString('en-US')
}

function signed(n) {
  return n >= 0 ? `+${fmt(n)}` : `−${fmt(Math.abs(n))}`
}

export default function TeamsView() {
  return (
    <main className="view">
      <div className="card-head standalone">
        <p className="year-summary">
          All 30 franchises, draft classes {WINDOW[0]}–{WINDOW[1]}, ranked by
          career minutes their picks delivered above slot expectation.
        </p>
        <p className="era-note muted">
          Credited to the selecting franchise — Dirk counts for Milwaukee,
          Kobe for Charlotte. Relocated teams carry their full lineage.
        </p>
      </div>

      <div className="table-wrap">
        <table className="league">
          <caption className="sr-only">
            Franchises ranked by NBA career minutes above draft-slot expectation
          </caption>
          <thead>
            <tr>
              <th className="col-pos" scope="col">#</th>
              <th scope="col">Franchise</th>
              <th className="num" scope="col">Picks</th>
              <th className="num hide-phone" scope="col">Avg pick</th>
              <th className="num hide-phone" scope="col">Hits</th>
              <th className="num hide-sm" scope="col">Career min</th>
              <th className="num" scope="col">Above slot</th>
            </tr>
          </thead>
          <tbody>
            {TEAMS.map((t, i) => (
              <tr key={t.team}>
                <td className="col-pos">{i + 1}</td>
                <td>{t.team}</td>
                <td className="num">{t.picks}</td>
                <td className="num hide-phone">{t.avg_pick}</td>
                <td className="num hide-phone">{t.hits}</td>
                <td className="num hide-sm">{fmt(t.total_min)}</td>
                <td className={`num ${t.value_added >= 0 ? 'val-up' : 'val-down'}`}>
                  {signed(t.value_added)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="section-head">Biggest steals</h2>
      <div className="table-wrap">
        <table className="league">
          <caption className="sr-only">
            Players whose careers most outran their draft slot
          </caption>
          <thead>
            <tr>
              <th className="col-pos" scope="col">Pick</th>
              <th scope="col">Player</th>
              <th className="hide-phone" scope="col">Year</th>
              <th scope="col">Drafted by</th>
              <th className="hide-sm" scope="col">From</th>
              <th className="num" scope="col">Above slot</th>
            </tr>
          </thead>
          <tbody>
            {STEALS.map((s) => (
              <tr key={`${s.year}-${s.pick}`}>
                <td className="col-pos">{s.pick}</td>
                <td>{s.player}</td>
                <td className="hide-phone">{s.year}</td>
                <td>{s.team}</td>
                <td className="hide-sm">{s.college}</td>
                <td className="num val-up">{signed(s.value_added)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}
