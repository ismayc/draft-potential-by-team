import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import App from '../src/App.jsx'
import { DRAFT_YEARS } from '../src/data/drafts.js'

const newest = Math.max(...DRAFT_YEARS)

function setUrl(search) {
  window.history.replaceState(null, '', search ? `/?${search}` : '/')
}

describe('App', () => {
  it('lands on the lottery view for the newest draft', () => {
    setUrl('')
    render(<App />)
    expect(screen.getByRole('button', { name: 'Lottery' })).toHaveAttribute(
      'aria-current',
      'page'
    )
    expect(screen.getByText(new RegExp(`won the ${newest} lottery`))).toBeInTheDocument()
  })

  it('switches views and mirrors the choice into the URL', async () => {
    setUrl('')
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Draft board' }))
    expect(screen.getByText('Round 2')).toBeInTheDocument()
    expect(window.location.search).toBe('?view=draft')

    await user.click(screen.getByRole('button', { name: 'About' }))
    expect(screen.getByText('What this is')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Lottery' }))
    expect(window.location.search).toBe('')
  })

  it('honours a deep link with view and year', () => {
    setUrl('view=draft&year=1993')
    render(<App />)
    expect(screen.getByRole('button', { name: 'Draft board' })).toHaveAttribute(
      'aria-current',
      'page'
    )
    expect(screen.getByDisplayValue('1993')).toBeInTheDocument()
  })

  it('falls back to the newest year for a year outside the data', () => {
    setUrl('year=1962')
    render(<App />)
    expect(screen.getByDisplayValue(String(newest))).toBeInTheDocument()
  })

  it('changes year from the picker and writes it to the URL', async () => {
    setUrl('')
    const user = userEvent.setup()
    render(<App />)
    await user.selectOptions(screen.getByLabelText('Draft year'), '2003')
    expect(screen.getByText(/won the 2003 lottery/)).toBeInTheDocument()
    expect(window.location.search).toBe('?year=2003')
    setUrl('')
  })

  it('toggles the theme and persists it', async () => {
    setUrl('')
    const user = userEvent.setup()
    render(<App />)
    const toggle = screen.getByRole('button', { name: /switch to light theme/i })
    await user.click(toggle)
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(localStorage.getItem('dpt:theme')).toBe('light')
    await user.click(screen.getByRole('button', { name: /switch to dark theme/i }))
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('still themes the session when localStorage is unavailable', async () => {
    setUrl('')
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('private mode')
    })
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('button', { name: /switch to light theme/i }))
    expect(document.documentElement.dataset.theme).toBe('light')
  })
})
