/**
 * The URL is the app's shared state. There is no router — two query
 * parameters describe everything a viewer can choose (which view, which
 * draft year), so any state worth reaching is shareable.
 *
 * Only non-default values are written, so a first-time visitor's URL stays
 * clean and a shared link carries exactly the choices its sender made.
 */

export const VIEWS = ['lottery', 'draft', 'about']

const DEFAULTS = {
  view: 'lottery',
  year: null, // null renders the newest available year
}

export function readState(search = window.location.search) {
  const q = new URLSearchParams(search)
  const view = q.get('view')
  const year = q.get('year')

  return {
    view: VIEWS.includes(view) ? view : DEFAULTS.view,
    year: year && /^\d{4}$/.test(year) ? Number(year) : DEFAULTS.year,
  }
}

export function writeState(state) {
  const q = new URLSearchParams()
  if (state.view !== DEFAULTS.view) q.set('view', state.view)
  if (state.year) q.set('year', String(state.year))

  const qs = q.toString()
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname
  // replaceState, not pushState: switching views shouldn't stack up history
  // entries that make the browser back button feel broken.
  window.history.replaceState(null, '', url)
}
