<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Plan, PlanNode } from '../../domain/models'
import { descendants, displayCode } from '../../domain/plans'
import { t, duration } from '../../i18n'
import UiButton from '../../ui/UiButton.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import Icon from '../../ui/Icon.vue'

export type TreeAction = 'record' | 'edit' | 'addTask' | 'addGroup' | 'category' | 'delete' | 'complete'
const props = withDefaults(defineProps<{ plan: Plan; parentId?: string | null; selected?: string }>(), { parentId: null, selected: '' })
const emit = defineEmits<{ action: [action: TreeAction, node: PlanNode] }>()
const collapsed = ref(new Set<string>())
watch(() => props.selected, selected => {
  for (const id of collapsed.value) if (descendants(props.plan, id).some(node => node.id === selected)) collapsed.value.delete(id)
})
const nodes = computed(() => props.plan.nodes.filter(node => node.parentId === props.parentId && !node.deletedAt).sort((a, b) => a.order - b.order))
function toggle(id: string) { if (collapsed.value.has(id)) collapsed.value.delete(id); else collapsed.value.add(id) }
function menu(node: PlanNode) {
  const items = [
    { label: t('common.edit'), icon: 'edit', action: () => emit('action', 'edit', node) },
    { label: t('plans.assignCategory'), icon: 'tag', action: () => emit('action', 'category', node) },
  ]
  if (node.kind !== 'task') items.unshift(
    { label: t('plans.addTask'), icon: 'plus', action: () => emit('action', 'addTask', node) },
    { label: t('plans.addGroup'), icon: 'plans', action: () => emit('action', 'addGroup', node) },
  )
  return [...items, { label: t('common.delete'), icon: 'delete', danger: true, action: () => emit('action', 'delete', node) }]
}
</script>
<template>
  <div :class="{ 'tree-nested': parentId !== null }">
    <div v-for="node in nodes" :key="node.id" class="tree-group" :data-node-id="node.id" :data-selected="selected === node.id || undefined">
      <div class="tree-row">
        <button v-if="node.kind === 'task'" type="button" class="todo-check" :aria-pressed="Boolean(node.completedAt)" :aria-label="(node.completedAt ? t('todos.reopen') : t('todos.complete')) + ': ' + node.title" :disabled="Boolean(plan.archivedAt)" @click="emit('action', 'complete', node)"><Icon v-if="node.completedAt" name="check" :size="16" /></button>
        <UiButton v-else variant="ghost" icon :aria-label="node.title" :aria-expanded="!collapsed.has(node.id)" @click="toggle(node.id)"><Icon :name="collapsed.has(node.id) ? 'next' : 'expand'" :size="18" /></UiButton>
        <div class="tree-title"><p class="row-title" :class="{ 'todo-complete': node.completedAt }"><span v-if="node.kind === 'task'" class="muted small">{{ displayCode(plan, node.id) }} · </span>{{ node.title }}</p><p v-if="node.description" class="row-detail">{{ node.description }}</p><p v-if="node.estimatedMinutes" class="row-detail">{{ duration(node.estimatedMinutes) }}</p></div>
        <div v-if="!plan.archivedAt" class="tree-actions"><UiButton v-if="node.kind === 'task'" variant="ghost" icon :aria-label="t('plans.recordProgress') + ': ' + node.title" @click="emit('action', 'record', node)"><Icon name="log" :size="18" /></UiButton><ActionMenu :items="menu(node)" /></div>
      </div>
      <PlanTree v-if="node.kind !== 'task' && !collapsed.has(node.id)" :plan="plan" :parent-id="node.id" :selected="selected" @action="(action, target) => emit('action', action, target)" />
    </div>
  </div>
</template>

