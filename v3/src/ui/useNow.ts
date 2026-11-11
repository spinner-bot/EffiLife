import { onMounted, onUnmounted, ref } from 'vue'
export function useNow() {
  const now = ref(new Date().toISOString())
  let timer: ReturnType<typeof setInterval> | undefined
  onMounted(() => { timer = setInterval(() => { now.value = new Date().toISOString() }, 30000) })
  onUnmounted(() => { if (timer) clearInterval(timer) })
  return now
}

