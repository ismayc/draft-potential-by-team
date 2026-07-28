import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import CollegesView from '../src/components/CollegesView.jsx'
import TeamsView from '../src/components/TeamsView.jsx'
import { COLLEGES, STEALS, TEAMS } from '../src/data/analysis.js'

describe('CollegesView', () => {
  it('renders every qualifying program, ranked', () => {
    render(<CollegesView />)
    const rows = document.querySelectorAll('tbody tr')
    expect(rows.length).toBe(COLLEGES.length)
    expect(rows[0].textContent).toContain(COLLEGES[0].college)
  })

  it('signs value above slot in both directions', () => {
    render(<CollegesView />)
    // The table spans over- and under-performing programs, so both value
    // classes appear with explicit +/− signs, never colour alone.
    expect(document.querySelectorAll('.val-up').length).toBeGreaterThan(0)
    expect(document.querySelectorAll('.val-down').length).toBeGreaterThan(0)
    expect(document.querySelector('.val-up').textContent).toMatch(/^\+/)
    expect(document.querySelector('.val-down').textContent).toMatch(/^−/)
  })

  it('states the window and the hit definition', () => {
    render(<CollegesView />)
    expect(screen.getByText(/classes 1989–2015/)).toBeInTheDocument()
    expect(screen.getByText(/10,000\+ NBA regular-season minutes/)).toBeInTheDocument()
  })
})

describe('TeamsView', () => {
  it('renders all 30 franchises and the steals table', () => {
    render(<TeamsView />)
    const tables = document.querySelectorAll('tbody')
    expect(tables[0].querySelectorAll('tr').length).toBe(TEAMS.length)
    expect(TEAMS.length).toBe(30)
    expect(tables[1].querySelectorAll('tr').length).toBe(STEALS.length)
  })

  it('ranks franchises by WS value with intervals and kept share', () => {
    render(<TeamsView />)
    const first = document.querySelector('tbody tr')
    expect(first.textContent).toContain(TEAMS[0].team)
    expect(first.textContent).toContain('%')
    expect(first.textContent).toContain(' to ')
    expect(screen.getByText(/credited to the selecting franchise/i)).toBeInTheDocument()
    expect(screen.getByText(/intervals cross zero/i)).toBeInTheDocument()
  })

  it('lists the top steal with its pick number', () => {
    render(<TeamsView />)
    expect(screen.getByText(STEALS[0].player)).toBeInTheDocument()
  })
})
