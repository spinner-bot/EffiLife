import { ref } from 'vue'

export type ConfirmTone = 'default' | 'danger'

export interface ConfirmOptions {
  tone?: ConfirmTone
}

export interface ConfirmRequest {
  id: number
  message: string
  tone: ConfirmTone
  resolve: (confirmed: boolean) => void
}

export const activeConfirm = ref<ConfirmRequest | null>(null)
let nextConfirmId = 1

export function requestConfirm(message: string, options: ConfirmOptions = {}): Promise<boolean> {
  if (activeConfirm.value) activeConfirm.value.resolve(false)
  return new Promise((resolve) => {
    activeConfirm.value = {
      id: nextConfirmId++,
      message,
      tone: options.tone || 'default',
      resolve,
    }
  })
}

export function settleConfirm(confirmed: boolean): void {
  const request = activeConfirm.value
  if (!request) return
  activeConfirm.value = null
  request.resolve(confirmed)
}
