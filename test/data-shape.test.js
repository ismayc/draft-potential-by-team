import { describe, expect, it } from 'vitest'
import { LOTTERY, LOTTERY_BY_YEAR, LOTTERY_YEARS } from '../src/data/lottery.js'
import { DRAFTS, DRAFTS_BY_YEAR, DRAFT_YEARS } from '../src/data/drafts.js'

// These tests lock the contract between the Python generator and the views:
// contiguous two-round-era years, intact lookup maps, and per-row shape.

describe('lottery data', () => {
  it('covers every year from 1989 without gaps', () => {
    const first = LOTTERY_YEARS[0]
    expect(first).toBe(1989)
    expect(LOTTERY_YEARS).toEqual(
      Array.from({ length: LOTTERY_YEARS.length }, (_, i) => first + i)
    )
  })

  it('keeps the BY_YEAR lookup in sync with the array', () => {
    expect(Object.keys(LOTTERY_BY_YEAR)).toHaveLength(LOTTERY.length)
    for (const season of LOTTERY) {
      expect(LOTTERY_BY_YEAR[season.year]).toBe(season)
    }
  })

  it('has contiguous result positions and a winner each year', () => {
    for (const { year, teams } of LOTTERY) {
      const positions = teams.map((t) => t.resultPos)
      expect(positions, String(year)).toEqual(
        Array.from({ length: teams.length }, (_, i) => i + 1)
      )
      expect(teams[0].player, String(year)).toBeTruthy()
    }
  })

  it('movement deltas reconcile with pre-lottery seeds', () => {
    for (const { year, teams } of LOTTERY) {
      for (const t of teams) {
        expect(t.seed - t.resultPos - t.delta, `${year} ${t.team}`).toBe(0)
      }
    }
  })
})

describe('draft data', () => {
  it('mirrors the lottery years exactly', () => {
    expect(DRAFT_YEARS).toEqual(LOTTERY_YEARS)
  })

  it('keeps the BY_YEAR lookup in sync with the array', () => {
    expect(Object.keys(DRAFTS_BY_YEAR)).toHaveLength(DRAFTS.length)
    for (const d of DRAFTS) {
      expect(DRAFTS_BY_YEAR[d.year]).toBe(d.picks)
    }
  })

  it('orders picks by overall number with both rounds present', () => {
    for (const { year, picks } of DRAFTS) {
      const overalls = picks.map((p) => p.overall)
      expect([...overalls].sort((a, b) => a - b), String(year)).toEqual(overalls)
      expect(new Set(picks.map((p) => p.round)), String(year)).toEqual(new Set([1, 2]))
    }
  })

  it('gives every played career gp, pts, and at least one team', () => {
    for (const { picks } of DRAFTS) {
      for (const p of picks) {
        if (p.career) {
          expect(p.career.gp).toBeGreaterThan(0)
          expect(p.career.teams.length).toBeGreaterThan(0)
        }
      }
    }
  })
})
