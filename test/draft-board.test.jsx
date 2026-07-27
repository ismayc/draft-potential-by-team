import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import DraftBoardView from '../src/components/DraftBoardView.jsx'

// Mocked board data: one pick with a full career, one that never played,
// one with no listed organization. This keeps both career branches covered
// whatever state the real harvest is in.
vi.mock('../src/data/drafts.js', () => {
  const picks = [
    {
      overall: 1,
      round: 1,
      roundPick: 1,
      player: 'Alpha Star',
      personId: 1,
      team: 'Phoenix Suns',
      org: 'Kansas',
      orgType: 'College/University',
      career: { gp: 1200, min: 40000, pts: 25000, seasons: 15, teams: ['PHX', 'LAL'] },
    },
    {
      overall: 31,
      round: 2,
      roundPick: 1,
      player: 'Beta Bench',
      personId: 2,
      team: 'Boston Celtics',
      org: '',
      orgType: '',
      career: null,
    },
  ]
  return {
    DRAFTS: [{ year: 1999, picks }],
    DRAFTS_BY_YEAR: { 1999: picks },
    DRAFT_YEARS: [1999],
  }
})

describe('DraftBoardView', () => {
  it('renders both rounds with separators', () => {
    render(<DraftBoardView year={1999} />)
    expect(screen.getByText('Round 1')).toBeInTheDocument()
    expect(screen.getByText('Round 2')).toBeInTheDocument()
  })

  it('shows career totals and the franchise list for players who played', () => {
    render(<DraftBoardView year={1999} />)
    expect(screen.getByText('Alpha Star')).toBeInTheDocument()
    expect(screen.getByText('1,200')).toBeInTheDocument()
    expect(screen.getByText('25,000')).toBeInTheDocument()
    expect(screen.getByText('PHX, LAL')).toBeInTheDocument()
  })

  it('shows dashes, not zeros, for a pick that never played', () => {
    render(<DraftBoardView year={1999} />)
    const row = screen.getByText('Beta Bench').closest('tr')
    expect(row.textContent).toContain('—')
    expect(row.textContent).not.toContain('0')
  })

  it('explains the dashes in a footnote', () => {
    render(<DraftBoardView year={1999} />)
    expect(screen.getByText(/never appeared in an NBA regular-season game/)).toBeInTheDocument()
  })
})
