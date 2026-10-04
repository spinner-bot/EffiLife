/** Runtime capabilities shared by gateway and archive services. */

import { translate } from '@/i18n'
import { isTauri as tauriIsTauri } from '@tauri-apps/api/core'

export type PlanRuntime = 'desktop-sidecar' | 'browser-service' | 'mobile-unavailable'

export function isMobilePlatform(): boolean {
  if (typeof navigator === 'undefined') return false
  const userAgentData = (navigator as Navigator & { userAgentData?: { mobile?: boolean } }).userAgentData
  return userAgentData?.mobile === true
    || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
}

export function isTauriRuntime(): boolean {
  return tauriIsTauri()
}

export function getPlanRuntime(): PlanRuntime {
  // The mobile runtime has no desktop sidecar, but it can still use the
  // local snapshot gateway. The legacy value is retained for protocol
  // compatibility; callers should use isMobilePlanRuntime() for clarity.
  if (isMobilePlatform()) return 'mobile-unavailable'
  if (isTauriRuntime()) return 'desktop-sidecar'
  return 'browser-service'
}

/** Whether PH is running in the mobile-local snapshot mode. */
export function isMobilePlanRuntime(): boolean {
  return getPlanRuntime() === 'mobile-unavailable'
}

export function getPlanRuntimeUnavailableReason(): string {
  return translate('plans.mobileRuntimeUnavailable')
}
