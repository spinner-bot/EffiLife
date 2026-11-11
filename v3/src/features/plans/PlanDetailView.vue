<script setup lang="ts">
import { computed, nextTick, reactive, ref, shallowRef, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import type { NodeKind, PlanNode, ProgressLog } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { planProgress, displayCode, categoryFor } from '../../domain/plans'
import { planMinutes } from '../../domain/selectors'
import { dateKey } from '../../domain/time'
import { t, duration, calendarDate, clock, categoryName, errorMessage } from '../../i18n'
import { openRecord, notify, confirmAction } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import UiDialog from '../../ui/UiDialog.vue'
import Panel from '../../ui/Panel.vue'
import EmptyState from '../../ui/EmptyState.vue'
import Icon from '../../ui/Icon.vue'
import TextEditorDialog from '../../ui/TextEditorDialog.vue'
import PlanTree, { type TreeAction } from './PlanTree.vue'
import NodeEditor from './NodeEditor.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import LogEditor from './LogEditor.vue'

const route = useRoute()
const plan = computed(() => current.value.plans.find(item => item.id === route.params.id))
const progress = computed(() => plan.value ? planProgress(plan.value) : { total: 0, completed: 0, percent: 0, logs: 0 })
const editor = reactive({ open: false, parentId: null as string | null, kind: 'task' as NodeKind, node: undefined as PlanNode | undefined })
const renaming = ref(false)
const categoryTarget = ref<PlanNode>()
const categoryId = ref('life')
const overwrite = ref(false)
const categoryError = ref('')
const selected = computed(() => String(route.query.task || ''))
const selectedLog = computed(() => String(route.query.log || ''))
const editingLog = shallowRef<ProgressLog>()
const logs = computed(() => [...(plan.value?.logs || [])].filter(log => !selected.value || log.taskId === selected.value).sort((a, b) => Date.parse(b.occurredAt) - Date.parse(a.occurredAt)))
watch([selected, selectedLog, () => plan.value?.id], async () => {
  await nextTick()
  const selector = selectedLog.value ? '[data-log-id="' + CSS.escape(selectedLog.value) + '"]' : selected.value ? '[data-node-id="' + CSS.escape(selected.value) + '"]' : ''
  if (selector) document.querySelector<HTMLElement>(selector)?.scrollIntoView({ block: 'center' })
}, { immediate: true, flush: 'post' })
function logDate(log: ProgressLog) { const record = current.value.records.find(item => log.recordIds.includes(item.id)); return dateKey(record?.startAt || log.occurredAt, current.value.preferences.timeZone) }
async function deleteLog(log: ProgressLog) {
  if (!plan.value || !await confirmAction(t('plans.deleteLog'), t('plans.deleteLogBody'))) return
  try { await dispatch({ type: 'deleteLog', planId: plan.value.id, logId: log.id }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
function logMenu(log: ProgressLog) { return [{ label: t('plans.editLog'), icon: 'edit', action: () => { editingLog.value = log } }, { label: t('plans.deleteLog'), icon: 'delete', danger: true, action: () => deleteLog(log) }] }
function add(kind: NodeKind, parentId: string | null = null) { Object.assign(editor, { open: true, parentId, kind, node: undefined }) }
async function action(type: TreeAction, node: PlanNode) {
  if (!plan.value) return
  if (type === 'record') { openRecord({ planId: plan.value.id, taskId: node.id }); return }
  if (type === 'edit') { Object.assign(editor, { open: true, parentId: node.parentId, kind: node.kind, node }); return }
  if (type === 'addTask' || type === 'addGroup') { add(type === 'addTask' ? 'task' : 'group', node.id); return }
  if (type === 'category') { categoryTarget.value = node; categoryId.value = categoryFor(plan.value, node.id); overwrite.value = false; categoryError.value = ''; return }
  try {
    if (type === 'complete') await dispatch({ type: 'setTaskCompletion', planId: plan.value.id, taskId: node.id, completed: !node.completedAt })
    if (type === 'delete' && await confirmAction(t('plans.deleteNodeConfirm'))) await dispatch({ type: 'deleteNode', planId: plan.value.id, nodeId: node.id })
  } catch (failure) { notify(errorMessage(failure), 'error') }
}
async function saveCategory() {
  if (!plan.value || !categoryTarget.value) return
  try { await dispatch({ type: 'assignCategory', planId: plan.value.id, nodeId: categoryTarget.value.id, categoryId: categoryId.value, overwrite: overwrite.value }); categoryTarget.value = undefined } catch (failure) { categoryError.value = errorMessage(failure) }
}
async function archive() {
  if (!plan.value) return
  try { await dispatch({ type: 'archivePlan', planId: plan.value.id, archived: !plan.value.archivedAt }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
async function rename(value: { title: string; description: string }) {
  if (plan.value) await dispatch({ type: 'updatePlan', planId: plan.value.id, ...value })
}
function logTime(log: { occurredAt: string; timePrecision?: string }) {
  if (log.timePrecision === 'date') return ''
  if (log.timePrecision === 'hour') return t('common.approxHour', { hour: clock(log.occurredAt, current.value.preferences.timeZone).split(':')[0]! })
  return clock(log.occurredAt, current.value.preferences.timeZone)
}
</script>
<template>
  <template v-if="plan">
    <RouterLink to="/plans" class="text-link" style="margin-bottom: var(--space-5)">{{ t('common.back') }} · {{ t('nav.plans') }}</RouterLink>
    <PageHeader :title="plan.title" :subtitle="plan.description">
      <UiButton variant="ghost" :aria-label="t('plans.rename')" @click="renaming = true"><Icon name="edit" :size="18" /></UiButton>
      <UiButton @click="archive"><Icon :name="plan.archivedAt ? 'restore' : 'archive'" :size="18" />{{ plan.archivedAt ? t('common.restore') : t('common.archive') }}</UiButton>
      <UiButton v-if="!plan.archivedAt" variant="primary" @click="openRecord({ planId: plan.id })"><Icon name="log" :size="18" />{{ t('plans.recordProgress') }}</UiButton>
    </PageHeader>
    <div class="stats-grid">
      <section class="panel stat"><div><p class="stat-label">{{ t('plans.structure') }}</p><strong class="stat-value">{{ progress.completed }} / {{ progress.total }}</strong></div><span class="stat-icon"><Icon name="done" /></span></section>
      <section class="panel stat"><div><p class="stat-label">{{ t('plans.logs') }}</p><strong class="stat-value">{{ plan.logs.length }}</strong></div><span class="stat-icon"><Icon name="log" /></span></section>
      <section class="panel stat"><div><p class="stat-label">{{ t('plans.totalTime') }}</p><strong class="stat-value">{{ duration(planMinutes(current, plan)) }}</strong></div><span class="stat-icon"><Icon name="time" /></span></section>
    </div>
    <div class="plan-detail-grid">
      <Panel :title="t('plans.structure')">
        <template #actions><div v-if="!plan.archivedAt" class="cluster"><UiButton variant="ghost" @click="add('section')"><Icon name="plus" :size="16" />{{ t('plans.addSection') }}</UiButton><UiButton variant="ghost" @click="add('task')"><Icon name="plus" :size="16" />{{ t('plans.addTask') }}</UiButton></div></template>
        <PlanTree v-if="plan.nodes.some(node => !node.deletedAt)" :plan="plan" :selected="selected" @action="action" />
        <EmptyState v-else :title="t('plans.noTasks')" icon="book"><UiButton v-if="!plan.archivedAt" @click="add('section')">{{ t('plans.addSection') }}</UiButton></EmptyState>
      </Panel>
      <Panel :title="t('plans.logs')">
        <template #actions><RouterLink v-if="selected" :to="{ name: 'plan', params: { id: plan.id } }" class="text-link">{{ t('common.all') }}</RouterLink></template>
        <div v-if="logs.length" class="panel-body">
          <div v-for="log in logs" :key="log.id" class="log-entry" :data-log-id="log.id" :data-selected="selectedLog === log.id">
            <div class="cluster spread small muted"><span>{{ calendarDate(dateKey(log.occurredAt, current.preferences.timeZone)) }} {{ logTime(log) }}</span><div class="cluster"><span v-if="log.kind === 'completion'" class="badge success">{{ t('plans.completed') }}</span><ActionMenu :items="logMenu(log)" /></div></div>
            <RouterLink v-if="log.taskId" :to="{ name: 'plan', params: { id: plan.id }, query: { task: log.taskId } }" class="text-link small">{{ displayCode(plan, log.taskId) }} · {{ plan.nodes.find(node => node.id === log.taskId)?.title }}</RouterLink>
            <p class="log-content">{{ log.content }}</p><p v-if="log.timingReference && !log.recordIds.length" class="small muted">{{ t('record.reference', { minutes: Math.round(log.timingReference.minutes) }) }}</p>
            <RouterLink v-if="log.recordIds.length" :to="{ path: '/time', query: { record: log.recordIds[0], date: logDate(log) } }" class="text-link small">{{ t('home.viewTime') }}<Icon name="arrow" :size="14" /></RouterLink>
          </div>
        </div>
        <EmptyState v-else :title="t('plans.noLogs')" icon="log" />
      </Panel>
    </div>
    <NodeEditor :open="editor.open" :plan-id="plan.id" :node="editor.node" :parent-id="editor.parentId" :kind="editor.kind" @close="editor.open = false" />
    <LogEditor :plan-id="plan.id" :log="editingLog" @close="editingLog = undefined" />
    <TextEditorDialog :open="renaming" :title="t('plans.rename')" :initial-title="plan.title" :initial-description="plan.description" :save="rename" @close="renaming = false" />
    <UiDialog :open="Boolean(categoryTarget)" :title="t('plans.assignCategory')" :description="categoryTarget?.title" @close="categoryTarget = undefined">
      <form class="stack" @submit.prevent="saveCategory"><label class="field"><span>{{ t('form.category') }}</span><select v-model="categoryId" class="select"><option v-for="item in current.categories" :key="item.id" :value="item.id">{{ categoryName(item) }}</option></select></label><label class="check-field"><input v-model="overwrite" type="checkbox" /><span>{{ t('plans.overwrite') }}</span></label><p v-if="categoryError" class="form-error" role="alert">{{ categoryError }}</p><div class="dialog-footer"><UiButton type="submit" variant="primary">{{ t('common.save') }}</UiButton></div></form>
    </UiDialog>
  </template>
  <EmptyState v-else :title="t('plans.notFound')" icon="plans"><RouterLink to="/plans" class="text-link">{{ t('common.back') }}</RouterLink></EmptyState>
</template>

