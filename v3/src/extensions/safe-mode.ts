/** The query works even when saved theme styles make the regular UI unusable. */
export const safeMode = typeof location !== 'undefined' && new URLSearchParams(location.search).get('safe') === '1'
export function enterSafeMode() {
  const url = new URL(location.href)
  url.searchParams.set('safe', '1')
  url.hash = '/settings'
  location.assign(url.href)
}
export function leaveSafeMode() {
  const url = new URL(location.href)
  url.searchParams.delete('safe')
  location.assign(url.href)
}

