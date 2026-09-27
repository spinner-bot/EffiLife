import { PLAN_HELPER_ORIGIN } from './runtimeConfig'

/** A local tombstone prevents an offline reset from being undone by stale server data. */
export const PLAN_HELPER_RESET_PENDING_KEY = 'effilife_plan_helper_reset_pending'
const RESET_TIMEOUT_MS = 4000

export function markPlanHelperResetPending(): void {
  localStorage.setItem(PLAN_HELPER_RESET_PENDING_KEY, '1')
}

export function clearPlanHelperResetPending(): void {
  localStorage.removeItem(PLAN_HELPER_RESET_PENDING_KEY)
}

export function hasPendingPlanHelperReset(): boolean {
  return localStorage.getItem(PLAN_HELPER_RESET_PENDING_KEY) === '1'
}

/**
 * Flush an offline reset before any normal Plan Helper read/write.
 * The caller intentionally receives the failure so stale server data is not
 * silently accepted as current data.
 */
export async function syncPendingPlanHelperReset(): Promise<void> {
  if (!hasPendingPlanHelperReset()) return

  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), RESET_TIMEOUT_MS)
  try {
    const response = await fetch(`${PLAN_HELPER_ORIGIN}/api/data/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ plans: [], replace: true }),
      signal: controller.signal,
    })
    const payload = await response.json() as { success?: boolean; error?: string }
    if (!response.ok || !payload.success) {
      throw new Error(payload.error || `计划重置同步失败（${response.status}）`)
    }
    clearPlanHelperResetPending()
  } finally {
    window.clearTimeout(timeout)
  }
}
