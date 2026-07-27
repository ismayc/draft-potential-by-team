import { LOTTERY_BY_YEAR } from '../data/lottery.js'

/**
 * One year's lottery: the pre-lottery odds each team carried in, the order
 * the envelopes/ping-pong balls actually produced, and who moved.
 *
 * Movement is never colour alone: the arrow glyph and the signed number
 * travel together, so the story survives grayscale and screen readers.
 */

function eraNote(year) {
  if (year === 1989) {
    return 'Unweighted era: every non-playoff team had an equal chance at the No. 1 pick.'
  }
  if (year <= 1993) {
    return 'Weighted lottery: 66 chances split by inverse record; the top three picks were drawn, the rest slotted by record.'
  }
  if (year <= 2018) {
    return '1,000-combination weighted lottery for the top three picks; remaining teams slotted by record.'
  }
  return 'Flattened odds: the three worst records share the best odds (14.0%) and the top four picks are drawn.'
}

function Movement({ delta }) {
  if (delta > 0) {
    return <span className="move move-up">▲ +{delta}</span>
  }
  if (delta < 0) {
    return <span className="move move-down">▼ −{Math.abs(delta)}</span>
  }
  return <span className="move move-hold">• held</span>
}

export default function LotteryView({ year }) {
  const data = LOTTERY_BY_YEAR[year]
  const winner = data.teams.find((t) => t.resultPos === 1)

  return (
    <main className="view">
      <div className="card-head standalone">
        <p className="year-summary">
          <strong>{winner.team}</strong> won the {year} lottery from {winner.oddsPct}% odds
          {winner.delta > 0 && <>, jumping {winner.delta} spots,</>} and selected{' '}
          <strong>{winner.player}</strong>.
        </p>
        <p className="era-note muted">{eraNote(year)}</p>
      </div>

      <div className="table-wrap">
        <table className="league">
          <caption className="sr-only">
            {year} NBA draft lottery odds and results
          </caption>
          <thead>
            <tr>
              <th className="col-pos" scope="col">Pick</th>
              <th className="col-team" scope="col">Team</th>
              <th className="hide-phone" scope="col">Record</th>
              <th scope="col">Odds</th>
              <th className="hide-sm" scope="col">Chances</th>
              <th scope="col">Move</th>
              <th className="col-player" scope="col">Selection</th>
            </tr>
          </thead>
          <tbody>
            {data.teams.map((t) => (
              <tr key={t.resultPos} className={t.resultPos === 1 ? 'zone-winner' : ''}>
                <td className="col-pos">{t.resultPos}</td>
                <td className="col-team">
                  {t.team}
                  {t.resultPos === 1 && (
                    <span className="crown" title="Lottery winner">★</span>
                  )}
                </td>
                <td className="hide-phone">{t.record}</td>
                <td>{t.oddsPct}%</td>
                <td className="hide-sm">{t.chances}</td>
                <td>
                  <Movement delta={t.delta} />
                </td>
                <td className="col-player">{t.player}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}
