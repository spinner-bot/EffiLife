/** Runtime capabilities shared by gateway and archive services. */

export type PlanRuntime = 'desktop-sidecar' | 'browser-service' | 'mobile-unavailable'

export function isMobilePlatform(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    typeof navigator === 'undefined' ? '' : navigator.userAgent,
  )
}

export function isTauriRuntime(): boolean {
  return typeof window !== 'undefined' && !!(window as Window & { __TAURI__?: unknown }).__TAURI__
}

export function getPlanRuntime(): PlanRuntime {
  if (isMobilePlatform()) return 'mobile-unavailable'
  if (isTauriRuntime()) return 'desktop-sidecar'
  return 'browser-service'
}

export function getPlanRuntimeUnavailableReason(): string {
  return '移动端暂未接入兼容原始 plan 模型的本地计划服务'
}
