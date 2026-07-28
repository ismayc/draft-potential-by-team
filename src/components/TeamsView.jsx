import { STEALS, TEAMS, WINDOW } from '../data/analysis.js'

/**
 * Which franchises have drafted best — all 30, ranked by career Win Shares
 * their picks delivered above slot expectation, with a 95% interval that
 * shows how much of the ordering is noise, and the share of drafted
 * careers' minutes each franchise kept. Value is credited to the selecting
 * franchise, draft-night trades included.
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
          career Win Shares their picks delivered above slot expectation.
        </p>
        <p className="era-note muted">
          Credited to the selecting franchise — Dirk counts for Milwaukee,
          Kobe for Charlotte. Kept share is the fraction of drafted
          careers&apos; minutes played for the drafting franchise. Most 95%
          intervals cross zero: the ordering is an estimate, not a verdict.
        </p>
      </div>

      <div className="table-wrap">
        <table className="league">
          <caption className="sr-only">
            Franchises ranked by NBA Win Shares above draft-slot expectation
          </caption>
          <thead>
            <tr>
              <th className="col-pos" scope="col">#</th>
              <th scope="col">Franchise</th>
              <th className="num hide-phone" scope="col">Picks</th>
              <th className="num hide-phone" scope="col">Avg pick</th>
              <th className="num" scope="col">WS above slot</th>
              <th className="num hide-sm" scope="col">95% interval</th>
              <th className="num" scope="col">Kept share</th>
            </tr>
          </thead>
          <tbody>
            {TEAMS.map((t, i) => (
              <tr key={t.team}>
                <td className="col-pos">{i + 1}</td>
                <td>{t.team}</td>
                <td className="num hide-phone">{t.picks}</td>
                <td className="num hide-phone">{t.avg_pick}</td>
                <td className={`num ${t.value_ws >= 0 ? 'val-up' : 'val-down'}`}>
                  {signed(t.value_ws)}
                </td>
                <td className="num hide-sm muted">
                  {fmt(t.ci_lo)} to {fmt(t.ci_hi)}
                </td>
                <td className="num">{Math.round(t.kept_share * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="section-head">Biggest steals</h2>
      <div className="table-wrap">
        <table className="league">
          <caption className="sr-only">
            Players whose careers most outran their draft slot, by Win Shares
          </caption>
          <thead>
            <tr>
              <th className="col-pos" scope="col">Pick</th>
              <th scope="col">Player</th>
              <th className="hide-phone" scope="col">Year</th>
              <th scope="col">Drafted by</th>
              <th className="hide-sm" scope="col">From</th>
              <th className="num" scope="col">WS above slot</th>
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
                <td className="num val-up">{signed(s.value_ws)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}
