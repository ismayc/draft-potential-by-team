import { Fragment } from 'react'
import { DRAFTS_BY_YEAR } from '../data/drafts.js'

/**
 * The full two-round board for one draft, with what each pick became:
 * games, minutes, points, seasons, and every franchise the player suited up
 * for. Picks that never reached an NBA floor show em dashes rather than
 * zeros — no games is an absence, not a stat line.
 */

function fmt(n) {
  return n == null ? '—' : n.toLocaleString('en-US')
}

export default function DraftBoardView({ year }) {
  const picks = DRAFTS_BY_YEAR[year]
  const rounds = [1, 2]

  return (
    <main className="view">
      <div className="table-wrap">
        <table className="league board">
          <caption className="sr-only">{year} NBA draft, both rounds</caption>
          <thead>
            <tr>
              <th className="col-pos" scope="col">Pick</th>
              <th className="col-player" scope="col">Player</th>
              <th scope="col">Drafted by</th>
              <th className="col-org" scope="col">From</th>
              <th className="num" scope="col">GP</th>
              <th className="num hide-phone" scope="col">MIN</th>
              <th className="num" scope="col">PTS</th>
              <th className="num hide-sm" scope="col">Seasons</th>
              <th className="col-teams hide-sm" scope="col">NBA teams</th>
            </tr>
          </thead>
          <tbody>
            {rounds.map((round) => (
              <Fragment key={round}>
                <tr className="round-sep">
                  <th colSpan={9} scope="colgroup">
                    Round {round}
                  </th>
                </tr>
                {picks
                  .filter((p) => p.round === round)
                  .map((p) => (
                    <tr key={p.overall}>
                      <td className="col-pos">{p.overall}</td>
                      <td className="col-player">{p.player}</td>
                      <td>{p.team}</td>
                      <td className="col-org">{p.org || '—'}</td>
                      <td className="num">{fmt(p.career && p.career.gp)}</td>
                      <td className="num hide-phone">{fmt(p.career && p.career.min)}</td>
                      <td className="num">{fmt(p.career && p.career.pts)}</td>
                      <td className="num hide-sm">{fmt(p.career && p.career.seasons)}</td>
                      <td className="col-teams hide-sm">
                        {p.career && p.career.teams.length ? p.career.teams.join(', ') : '—'}
                      </td>
                    </tr>
                  ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <p className="board-note muted">
        Career totals are regular-season, through the most recent completed
        season. A dash means the player never appeared in an NBA
        regular-season game.
      </p>
    </main>
  )
}
