/** Runtime endpoints shared by the unified workspace services. */

const DEFAULT_PLAN_HELPER_ORIGIN = 'http://127.0.0.1:8765'

function normalizeOrigin(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

export const PLAN_HELPER_ORIGIN = normalizeOrigin(
  import.meta.env.VITE_PLAN_HELPER_ORIGIN || DEFAULT_PLAN_HELPER_ORIGIN,
)
