<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { t } from '../i18n'
import Icon from './Icon.vue'
const props = defineProps<{ ids: string[] }>()
const emit = defineEmits<{ reorder: [ids: string[]] }>()
const root = ref<HTMLElement>(), dragging = ref(''), insertion = ref(0), y = ref(0), x = ref(0), height = ref(0), width = ref(0)
let startY = 0, startX = 0, offsetY = 0, offsetX = 0, pending = '', pointerId = -1
const visible = computed(() => {
  if (!dragging.value) return props.ids
  const ids = props.ids.filter(id => id !== dragging.value)
  ids.splice(insertion.value, 0, '__gap__')
  return ids
})
function start(event: PointerEvent, id: string) {
  if (event.button !== 0 || dragging.value) return
  const row = (event.currentTarget as HTMLElement).closest<HTMLElement>('[data-sort-id]')!
  const rect = row.getBoundingClientRect()
  height.value = rect.height; width.value = rect.width; offsetY = event.clientY - rect.top; offsetX = event.clientX - rect.left
  pending = id; pointerId = event.pointerId; startY = event.clientY; startX = event.clientX
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  window.addEventListener('pointermove', move); window.addEventListener('pointerup', release); window.addEventListener('pointercancel', cancel)
}
function move(event: PointerEvent) {
  if (event.pointerId !== pointerId) return
  if (!dragging.value && Math.hypot(event.clientY - startY, event.clientX - startX) < 5) return
  if (!dragging.value) { insertion.value = props.ids.indexOf(pending); dragging.value = pending }
  event.preventDefault(); y.value = event.clientY - offsetY; x.value = event.clientX - offsetX
  const rows = [...root.value!.querySelectorAll<HTMLElement>('[data-sort-id]')].filter(row => row.dataset.sortId !== '__gap__')
  insertion.value = rows.filter(row => { const rect = row.getBoundingClientRect(); return event.clientY > rect.top + rect.height / 2 }).length
  if (event.clientY < 70) window.scrollBy({ top: -16 })
  else if (event.clientY > innerHeight - 70) window.scrollBy({ top: 16 })
}
function cleanup() { pending = ''; pointerId = -1; window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', release); window.removeEventListener('pointercancel', cancel) }
function release(event: PointerEvent) {
  if (event.pointerId !== pointerId) return
  const id = dragging.value
  if (id) { const ids = props.ids.filter(item => item !== id); ids.splice(insertion.value, 0, id); emit('reorder', ids) }
  dragging.value = ''; cleanup()
}
function cancel() { dragging.value = ''; cleanup() }
function keyboard(event: KeyboardEvent, id: string) {
  if (!['ArrowUp', 'ArrowDown'].includes(event.key)) return
  event.preventDefault()
  const ids = [...props.ids], index = ids.indexOf(id), target = index + (event.key === 'ArrowUp' ? -1 : 1)
  if (target < 0 || target >= ids.length) return
  ids.splice(index, 1); ids.splice(target, 0, id); emit('reorder', ids)
}
onUnmounted(cleanup)
</script>
<template>
  <div ref="root"><TransitionGroup name="sort" tag="div"><div v-for="id in visible" :key="id" :data-sort-id="id" class="sortable-row" :class="{ 'sort-gap': id === '__gap__' }" :style="id === '__gap__' ? { height: height + 'px' } : undefined"><template v-if="id !== '__gap__'"><button type="button" class="drag-handle" :aria-label="t('common.reorder')" @pointerdown="start($event, id)" @keydown="keyboard($event, id)"><Icon name="drag" :size="19" /></button><div class="grow"><slot :id="id" /></div></template></div></TransitionGroup></div>
  <Teleport to="body"><div v-if="dragging" class="sort-ghost panel" :style="{ top: y + 'px', left: x + 'px', width: width + 'px', minHeight: height + 'px' }"><Icon name="drag" :size="19" /><div class="grow"><slot :id="dragging" /></div></div></Teleport>
</template>
<style>
.sortable-row { display: flex; align-items: center; gap: .5rem; min-height: 64px; padding: .5rem .75rem; border-bottom: 1px solid var(--line); }
.drag-handle { display: grid; place-items: center; padding: .5rem; border: 0; border-radius: .4rem; background: transparent; color: var(--muted); cursor: grab; touch-action: none; flex: 0 0 auto; }
.drag-handle:hover, .drag-handle:focus-visible { background: var(--subtle); color: var(--ink); }
.sort-gap { background: color-mix(in srgb, var(--muted) 14%, transparent); border: 1px dashed var(--muted); border-radius: var(--radius-sm); }
.sort-ghost { position: fixed; z-index: 900; pointer-events: none; opacity: .9; display: flex; align-items: center; gap: .75rem; padding: .5rem 1rem; box-shadow: 0 16px 40px #0003; }
.sort-move { transition: transform 220ms ease; }.sort-enter-active, .sort-leave-active { transition: opacity 150ms ease; }.sort-enter-from,.sort-leave-to { opacity: 0; }.sort-leave-active { position: absolute; }
@media (prefers-reduced-motion: reduce) { .sort-move,.sort-enter-active,.sort-leave-active { transition: none; } }
</style>
