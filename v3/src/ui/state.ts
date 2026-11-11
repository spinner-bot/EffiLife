import { reactive, shallowRef } from 'vue'

export const recording = reactive({ open: false, planId: '', taskId: '', sequence: 0 })
export function openRecord(context: { planId?: string; taskId?: string } = {}) {
  recording.planId = context.planId || ''
  recording.taskId = context.taskId || ''
  recording.sequence++
  recording.open = true
}
export interface Notice { id: number; message: string; kind: 'success' | 'error' }
export const notices = shallowRef<Notice[]>([])
let sequence = 0
export function notify(message: string, kind: Notice['kind'] = 'success') {
  const id = ++sequence
  notices.value = [...notices.value.slice(-2), { id, message, kind }]
  window.setTimeout(() => dismiss(id), kind === 'error' ? 9000 : 4500)
}
export function dismiss(id: number) { notices.value = notices.value.filter(item => item.id !== id) }

export const confirmation = shallowRef<{ title: string; description: string; resolve: (value: boolean) => void } | null>(null)
export function confirmAction(title: string, description = ''): Promise<boolean> {
  if (confirmation.value) confirmation.value.resolve(false)
  return new Promise(resolve => { confirmation.value = { title, description, resolve } })
}
export function finishConfirmation(value: boolean) {
  const current = confirmation.value
  confirmation.value = null
  current?.resolve(value)
}

