import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import LotteryView from '../src/components/LotteryView.jsx'

describe('LotteryView', () => {
  it('tells the 1993 story: Orlando from 1.5%, up 10, Chris Webber', () => {
    render(<LotteryView year={1993} />)
    expect(screen.getByText(/won the 1993 lottery from 1\.5% odds/)).toBeInTheDocument()
    expect(screen.getByText(/jumping 10 spots/)).toBeInTheDocument()
    expect(screen.getAllByText('▲ +10').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Chris Webber').length).toBeGreaterThan(0)
  })

  it('marks the winner row and never encodes movement with colour alone', () => {
    render(<LotteryView year={1993} />)
    expect(document.querySelector('.zone-winner')).not.toBeNull()
    // Every movement cell carries a glyph AND a signed number or word.
    for (const el of document.querySelectorAll('.move')) {
      expect(el.textContent).toMatch(/^(▲ \+\d+|▼ −\d+|• held)$/)
    }
    expect(document.querySelectorAll('.move-down').length).toBeGreaterThan(0)
  })

  it('renders held positions with a neutral marker', () => {
    // 2003: several teams held their inverse-record slot.
    render(<LotteryView year={2003} />)
    expect(document.querySelectorAll('.move-hold').length).toBeGreaterThan(0)
  })

  it('describes each odds era', () => {
    const notes = [
      [1989, /unweighted era/i],
      [1991, /66 chances/i],
      [2003, /1,000-combination/i],
      [2019, /flattened odds/i],
    ]
    for (const [year, note] of notes) {
      const { unmount } = render(<LotteryView year={year} />)
      expect(screen.getByText(note)).toBeInTheDocument()
      unmount()
    }
  })

  it('shows odds, chances, and record for every team', () => {
    render(<LotteryView year={2025} />)
    const rows = document.querySelectorAll('tbody tr')
    expect(rows.length).toBe(14)
    expect(screen.getAllByText(/%$/).length).toBe(14)
  })
})
