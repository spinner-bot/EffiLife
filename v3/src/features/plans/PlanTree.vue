<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import type { Plan, PlanNode } from '../../domain/models'
import { descendants, categoryFor } from '../../domain/plans'
import { dispatch } from '../../application/runtime'
import { t, duration, errorMessage } from '../../i18n'
import { notify } from '../../ui/state'
import { flattenTree, projectDrop } from './tree-projection'
import CategoryBadge from '../categories/CategoryBadge.vue'
import UiButton from '../../ui/UiButton.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import Icon from '../../ui/Icon.vue'
export type TreeAction = 'record' | 'edit' | 'addTask' | 'addGroup' | 'category' | 'delete' | 'complete'
const props = withDefaults(defineProps<{ plan: Plan; selected?: string }>(), { selected: '' })
const emit = defineEmits<{ action: [action: TreeAction, node: PlanNode] }>()
const root = ref<HTMLElement>(), collapsed = ref(new Set<string>()), dragging = ref(''), settling = ref(false)
const insertion = ref(0), horizontal = ref(0), x = ref(0), y = ref(0), width = ref(0), height = ref(0)
let startX = 0, startY = 0, offsetX = 0, offsetY = 0, initialDepth = 0, pointerId = -1, pending = '', indent = 24
let frame = 0, pointerY = 0
const omitted = computed(() => new Set(dragging.value ? [dragging.value, ...descendants(props.plan, dragging.value).map(node => node.id)] : []))
const rows = computed(() => flattenTree(props.plan, collapsed.value, omitted.value))
const projection = computed(() => projectDrop(rows.value, insertion.value, initialDepth + Math.round(horizontal.value / indent)))
const displayed = computed(() => {
  const values = rows.value.map(row => ({ ...row, id: row.node.id }))
  if (dragging.value) values.splice(insertion.value, 0, { node: props.plan.nodes.find(node => node.id === dragging.value)!, depth: projection.value.depth, id: '__gap__' })
  return values
})
const draggedNode = computed(() => props.plan.nodes.find(node => node.id === dragging.value))
watch(() => props.selected, selected => { for (const id of collapsed.value) if (descendants(props.plan, id).some(node => node.id === selected)) collapsed.value.delete(id) })
function toggle(id: string) { if (collapsed.value.has(id)) collapsed.value.delete(id); else collapsed.value.add(id) }
function menu(node: PlanNode) {
  const items = [
    { label: t('common.edit'), icon: 'edit', action: () => emit('action', 'edit', node) },
    { label: t(node.kind === 'task' ? 'plans.taskCategory' : 'plans.groupCategory'), icon: 'tag', action: () => emit('action', 'category', node) },
  ]
  if (node.kind !== 'task') items.unshift(
    { label: t('plans.addTask'), icon: 'plus', action: () => emit('action', 'addTask', node) },
    { label: t('plans.addGroup'), icon: 'plans', action: () => emit('action', 'addGroup', node) },
  )
  return [...items, { label: t('common.delete'), icon: 'delete', danger: true, action: () => emit('action', 'delete', node) }]
}
function start(event: PointerEvent, node: PlanNode, depth: number) {
  if (event.button !== 0 || props.plan.archivedAt || settling.value) return
  const row = (event.currentTarget as HTMLElement).closest<HTMLElement>('[data-node-id]')!
  const rect = row.getBoundingClientRect()
  width.value = rect.width; height.value = rect.height; offsetX = event.clientX - rect.left; offsetY = event.clientY - rect.top
  startX = event.clientX; startY = event.clientY; initialDepth = depth; pointerId = event.pointerId; pending = node.id
  indent = innerWidth <= 600 ? 16 : 24
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  window.addEventListener('pointermove', move); window.addEventListener('pointerup', release); window.addEventListener('pointercancel', cancel); window.addEventListener('keydown', escape)
}
function locate() {
  const elements = [...root.value!.querySelectorAll<HTMLElement>('[data-tree-row]')].filter(element => rows.value.some(row => row.node.id === element.dataset.treeRow))
  insertion.value = elements.filter(element => { const rect = element.getBoundingClientRect(); return pointerY > rect.top + rect.height / 2 }).length
}
function autoScroll() {
  if (!dragging.value || settling.value) return
  const delta = pointerY < 90 ? -Math.min(16, (90 - pointerY) / 4) : pointerY > innerHeight - 90 ? Math.min(16, (pointerY - innerHeight + 90) / 4) : 0
  if (delta) { window.scrollBy(0, delta); locate() }
  frame = requestAnimationFrame(autoScroll)
}
function move(event: PointerEvent) {
  if (event.pointerId !== pointerId || settling.value) return
  if (!dragging.value && Math.hypot(event.clientX - startX, event.clientY - startY) < 5) return
  if (!dragging.value) {
    insertion.value = rows.value.findIndex(row => row.node.id === pending)
    dragging.value = pending
    frame = requestAnimationFrame(autoScroll)
  }
  event.preventDefault()
  pointerY = event.clientY; horizontal.value = event.clientX - startX; x.value = event.clientX - offsetX; y.value = event.clientY - offsetY
  locate()
}
function cleanup() {
  cancelAnimationFrame(frame); pointerId = -1; pending = ''
  window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', release); window.removeEventListener('pointercancel', cancel); window.removeEventListener('keydown', escape)
}
async function release(event: PointerEvent) {
  if (event.pointerId !== pointerId) return
  cleanup()
  if (!dragging.value) return
  settling.value = true
  try {
    const target = projection.value
    await dispatch({ type: 'moveNode', planId: props.plan.id, nodeId: dragging.value, parentId: target.parentId, beforeId: target.beforeId })
    if (target.parentId) collapsed.value.delete(target.parentId)
  } catch (failure) { notify(errorMessage(failure), 'error') }
  finally { dragging.value = ''; settling.value = false; horizontal.value = 0 }
}
function cancel() { if (settling.value) return; dragging.value = ''; horizontal.value = 0; cleanup() }
function escape(event: KeyboardEvent) { if (event.key === 'Escape') { event.preventDefault(); cancel() } }
async function keyboard(event: KeyboardEvent, node: PlanNode) {
  if (!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.key) || settling.value) return
  event.preventDefault()
  const remaining = flattenTree(props.plan, collapsed.value, new Set([node.id, ...descendants(props.plan, node.id).map(child => child.id)]))
  const visible = flattenTree(props.plan, collapsed.value), original = visible.findIndex(row => row.node.id === node.id)
  const depth = visible[original]!.depth
  let index = Math.min(original, remaining.length), desired = depth
  if (event.key === 'ArrowUp') index = Math.max(0, index - 1)
  if (event.key === 'ArrowDown') index = Math.min(remaining.length, index + 1)
  if (event.key === 'ArrowLeft') desired--
  if (event.key === 'ArrowRight') desired++
  const target = projectDrop(remaining, index, desired)
  settling.value = true
  try { await dispatch({ type: 'moveNode', planId: props.plan.id, nodeId: node.id, parentId: target.parentId, beforeId: target.beforeId }); if (target.parentId) collapsed.value.delete(target.parentId) } catch (failure) { notify(errorMessage(failure), 'error') } finally { settling.value = false }
}
onUnmounted(cleanup)
</script>
<template>
  <div ref="root" class="plan-tree" :aria-busy="settling">
    <TransitionGroup name="tree-sort" tag="div">
      <div v-for="row in displayed" :key="row.id" class="tree-group" :class="{ 'tree-drop-gap': row.id === '__gap__' }" :data-node-id="row.id === '__gap__' ? undefined : row.id" :data-tree-row="row.id" :data-depth="row.depth" :data-selected="selected === row.id || undefined" :style="{ '--tree-depth': row.depth, minHeight: row.id === '__gap__' ? height + 'px' : undefined }">
        <div v-if="row.id === '__gap__'" class="tree-drop-caption">{{ t('plans.dropHere') }} · {{ projection.parentId ? plan.nodes.find(node => node.id === projection.parentId)?.title : t('plans.rootLevel') }}</div>
        <div v-else class="tree-row">
          <button v-if="!plan.archivedAt" type="button" class="drag-handle" :aria-label="t('plans.moveNode', { title: row.node.title })" :disabled="settling" @pointerdown="start($event, row.node, row.depth)" @keydown="keyboard($event, row.node)"><Icon name="drag" :size="18" /></button>
          <button v-if="row.node.kind === 'task'" type="button" class="todo-check" :aria-pressed="Boolean(row.node.completedAt)" :aria-label="(row.node.completedAt ? t('todos.reopen') : t('todos.complete')) + ': ' + row.node.title" :disabled="Boolean(plan.archivedAt)" @click="emit('action', 'complete', row.node)"><Icon v-if="row.node.completedAt" name="check" :size="16" /></button>
          <UiButton v-else variant="ghost" icon :aria-label="row.node.title" :aria-expanded="!collapsed.has(row.id)" @click="toggle(row.id)"><Icon :name="collapsed.has(row.id) ? 'next' : 'expand'" :size="18" /></UiButton>
          <div class="tree-title"><p class="row-title" :class="{ 'todo-complete': row.node.completedAt }"><CategoryBadge v-if="row.node.kind === 'task'" :category-id="categoryFor(plan, row.id)" /><span class="node-name">{{ row.node.title }}</span></p><p v-if="row.node.description" class="row-detail">{{ row.node.description }}</p><p v-if="row.node.estimatedMinutes" class="row-detail">{{ duration(row.node.estimatedMinutes) }}</p></div>
          <div v-if="!plan.archivedAt" class="tree-actions"><UiButton v-if="row.node.kind === 'task'" variant="ghost" icon :aria-label="t('plans.recordProgress') + ': ' + row.node.title" @click="emit('action', 'record', row.node)"><Icon name="log" :size="18" /></UiButton><ActionMenu :items="menu(row.node)" /></div>
        </div>
      </div>
    </TransitionGroup>
    <p class="sr-only" aria-live="polite">{{ dragging ? t('plans.dropLevel', { level: projection.depth + 1 }) : '' }}</p>
  </div>
  <Teleport to="body"><div v-if="draggedNode" class="tree-drag-ghost panel" :style="{ top: y + 'px', left: x + 'px', width: width + 'px' }"><Icon name="drag" :size="18" /><div><strong>{{ draggedNode.title }}</strong><p v-if="draggedNode.kind !== 'task'" class="small muted">{{ t('plans.movingSubtree', { count: omitted.size - 1 }) }}</p></div></div></Teleport>
</template>
<style scoped>
.plan-tree { --tree-indent: 24px; }.tree-group { margin-inline-start: min(calc(var(--tree-depth) * var(--tree-indent)), 45%); }.tree-row { padding-inline: .5rem; gap: .5rem; }.tree-title { min-width: 0; }.row-title { overflow-wrap: anywhere; }.tree-actions { flex-shrink: 0; }.tree-drop-gap { border: 1px dashed var(--muted); border-radius: var(--radius-sm); background: color-mix(in srgb, var(--muted) 14%, transparent); display: flex; align-items: center; padding-inline: 1rem; }.tree-drop-caption { color: var(--muted); font-size: var(--text-xs); }.tree-drag-ghost { position: fixed; z-index: 900; pointer-events: none; opacity: .92; box-shadow: 0 16px 40px #0003; display: flex; align-items: center; gap: .75rem; padding: 1rem; }.tree-sort-move { transition: transform 240ms cubic-bezier(.2,.75,.25,1); }.tree-sort-enter-active,.tree-sort-leave-active { transition: opacity 160ms ease; }.tree-sort-enter-from,.tree-sort-leave-to { opacity: 0; }.tree-sort-leave-active { position: absolute; }
@media(max-width:600px) { .plan-tree { --tree-indent: 16px; }.tree-row { gap: .2rem; }.drag-handle { padding: .4rem .2rem; }.tree-actions { gap: 0; } }
@media(prefers-reduced-motion:reduce) { .tree-sort-move,.tree-sort-enter-active,.tree-sort-leave-active { transition: none; } }
</style>
