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
  if (isMobilePlatform()) return 'mobile-unavailable'
  if (isTauriRuntime()) return 'desktop-sidecar'
  return 'browser-service'
}

export function getPlanRuntimeUnavailableReason(): string {
  return translate('plans.mobileRuntimeUnavailable')
}
