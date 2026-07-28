import { COLLEGES, WINDOW } from '../data/analysis.js'

/**
 * Which colleges produce the best NBA talent — every program with 8+
 * draftees in the window, ranked by career minutes their picks delivered
 * above the expectation for where they were taken. Numbers come from the
 * reconciled Python/R analysis pipeline, not from this app.
 */

function fmt(n) {
  return Math.round(n).toLocaleString('en-US')
}

function signed(n) {
  return n >= 0 ? `+${fmt(n)}` : `−${fmt(Math.abs(n))}`
}

export default function CollegesView() {
  return (
    <main className="view">
      <div className="card-head standalone">
        <p className="year-summary">
          Programs with 8+ draftees, classes {WINDOW[0]}–{WINDOW[1]}, ranked
          by career minutes delivered above slot expectation.
        </p>
        <p className="era-note muted">
          A hit is a career of 10,000+ NBA regular-season minutes. Later
          classes are excluded — they are still accumulating.
        </p>
      </div>

      <div className="table-wrap">
        <table className="league">
          <caption className="sr-only">
            Colleges ranked by NBA career minutes above draft-slot expectation
          </caption>
          <thead>
            <tr>
              <th className="col-pos" scope="col">#</th>
              <th scope="col">College</th>
              <th className="num" scope="col">Draftees</th>
              <th className="num hide-phone" scope="col">Hits</th>
              <th className="num" scope="col">Hit rate</th>
              <th className="num hide-sm" scope="col">Career min</th>
              <th className="num" scope="col">Above slot</th>
            </tr>
          </thead>
          <tbody>
            {COLLEGES.map((c, i) => (
              <tr key={c.college}>
                <td className="col-pos">{i + 1}</td>
                <td>{c.college}</td>
                <td className="num">{c.draftees}</td>
                <td className="num hide-phone">{c.hits}</td>
                <td className="num">{Math.round(c.hit_rate * 100)}%</td>
                <td className="num hide-sm">{fmt(c.total_min)}</td>
                <td className={`num ${c.value_added >= 0 ? 'val-up' : 'val-down'}`}>
                  {signed(c.value_added)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}
