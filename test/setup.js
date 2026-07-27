import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

// The app makes zero network requests — everything renders from committed
// data modules — so there is no fetch stub here on purpose. A test that
// sees a fetch happen has found a bug.

beforeEach(() => {
  // jsdom has no matchMedia; the pre-paint theme script needs it.
  // Defaulting `matches` to false selects the dark branch.
  if (!window.matchMedia) {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
  }
})

afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.restoreAllMocks()

  // The theme is written to the document element, which outlives cleanup().
  delete document.documentElement.dataset.theme
})
