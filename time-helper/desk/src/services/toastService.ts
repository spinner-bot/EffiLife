import { ref } from 'vue'

export type ToastTone = 'info' | 'success' | 'error'

export interface ToastMessage {
  id: number
  message: string
  tone: ToastTone
}

export const toastMessages = ref<ToastMessage[]>([])
let nextToastId = 1

export function notifyToast(message: string, tone: ToastTone = 'info', duration = 3800): number {
  const id = nextToastId++
  toastMessages.value = [...toastMessages.value, { id, message, tone }]
  if (duration > 0) {
    window.setTimeout(() => dismissToast(id), duration)
  }
  return id
}

export function dismissToast(id: number): void {
  toastMessages.value = toastMessages.value.filter((toast) => toast.id !== id)
}
