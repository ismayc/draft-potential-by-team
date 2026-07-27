import { describe, expect, it } from 'vitest'
import { readState, writeState, VIEWS } from '../src/utils/urlState.js'

describe('readState', () => {
  it('returns defaults for an empty query string', () => {
    expect(readState('')).toEqual({ view: 'lottery', year: null })
  })

  it('reads a valid view and year', () => {
    expect(readState('?view=draft&year=1993')).toEqual({ view: 'draft', year: 1993 })
  })

  it('rejects an unknown view', () => {
    expect(readState('?view=nonsense').view).toBe('lottery')
  })

  it('rejects a malformed year', () => {
    expect(readState('?year=93').year).toBeNull()
    expect(readState('?year=abcd').year).toBeNull()
  })

  it('exposes the view whitelist', () => {
    expect(VIEWS).toEqual(['lottery', 'draft', 'about'])
  })
})

describe('writeState', () => {
  it('writes nothing for the default state', () => {
    writeState({ view: 'lottery', year: null })
    expect(window.location.search).toBe('')
  })

  it('writes only non-default values', () => {
    writeState({ view: 'draft', year: 2003 })
    expect(window.location.search).toBe('?view=draft&year=2003')

    writeState({ view: 'lottery', year: 2003 })
    expect(window.location.search).toBe('?year=2003')
  })

  it('round-trips through readState', () => {
    writeState({ view: 'about', year: 1999 })
    expect(readState(window.location.search)).toEqual({ view: 'about', year: 1999 })
    // Leave the URL clean for the next test file.
    writeState({ view: 'lottery', year: null })
  })
})
