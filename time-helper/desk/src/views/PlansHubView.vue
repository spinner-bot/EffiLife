<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Check, ChevronRight, ClipboardList, Clock3, FolderPlus, Pencil, Plus, Trash2 } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import { useI18n } from '@/i18n'
import {
  addPlanSection,
  addPlanTask,
  archivePlan,
  completePlanTask,
  createEventPlan,
  deletePlanTask,
  getPlanFull,
  listPlanArchives,
  listPlanSummaries,
  restorePlanArchive,
  type PlanArchiveSummary,
  type PlanFull,
  type PlanSummary,
  updatePlanTask,
  updateEventPlan,
} from '@/services/planGateway'

const router = useRouter()
const { t, locale } = useI18n()
const view = ref<'hub' | 'events' | 'detail'>('hub')
const plans = ref<PlanSummary[]>([])
const archives = ref<PlanArchiveSummary[]>([])
const selectedPlan = ref<PlanFull | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')
const showCreate = ref(false)
const planName = ref('')
const planDate = ref(toDateInput(new Date()))
const editingMeta = ref(false)
const sectionName = ref('')
const sectionInfo = ref('')
const taskSectionIndex = ref<number | null>(null)
const editingTaskId = ref<string | null>(null)
const editingTaskSectionIndex = ref<number | null>(null)
const taskContent = ref('')
const taskMinutes = ref(30)

function toDateInput(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function toDateTuple(value: string): [number, number, number] {
  const [year, month, day] = value.split('-').map(Number)
  return [year, month, day]
}

function formatPlanDate(date?: [number, number, number]): string {
  if (!date) return ''
  const [year, month, day] = date
  return new Date(year, month - 1, day).toLocaleDateString(locale.value)
}

async function loadPlans() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [activePlans, archivedPlans] = await Promise.all([listPlanSummaries(), listPlanArchives()])
    plans.value = activePlans
    archives.value = archivedPlans
  } catch (error) {
    plans.value = []
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function archiveSelectedPlan() {
  if (!selectedPlan.value || !confirm(t('plans.archiveConfirm'))) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await archivePlan(planId)
    selectedPlan.value = null
    view.value = 'events'
    await loadPlans()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function restoreArchive(archive: PlanArchiveSummary) {
  isLoading.value = true
  errorMessage.value = ''
  try {
    await restorePlanArchive(archive.file)
    await loadPlans()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function openEvents() {
  view.value = 'events'
  await loadPlans()
}

async function openPlan(plan: PlanSummary) {
  isLoading.value = true
  errorMessage.value = ''
  try {
    selectedPlan.value = await getPlanFull(plan.id)
    view.value = 'detail'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function createPlan() {
  const name = planName.value.trim()
  if (!name || !planDate.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const created = await createEventPlan(name, toDateTuple(planDate.value))
    selectedPlan.value = await getPlanFull(created.id)
    showCreate.value = false
    planName.value = ''
    view.value = 'detail'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function savePlanMeta() {
  if (!selectedPlan.value || !planName.value.trim() || !planDate.value) return
  isLoading.value = true
  try {
    const planId = selectedPlan.value.id
    await updateEventPlan(planId, planName.value.trim(), toDateTuple(planDate.value))
    selectedPlan.value = await getPlanFull(planId)
    editingMeta.value = false
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

function startMetaEdit() {
  if (!selectedPlan.value) return
  planName.value = selectedPlan.value.name
  planDate.value = selectedPlan.value.date ? `${selectedPlan.value.date[0]}-${String(selectedPlan.value.date[1]).padStart(2, '0')}-${String(selectedPlan.value.date[2]).padStart(2, '0')}` : toDateInput(new Date())
  editingMeta.value = true
}

async function saveSection() {
  if (!selectedPlan.value || !sectionName.value.trim()) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await addPlanSection(planId, sectionName.value.trim(), sectionInfo.value.trim())
    sectionName.value = ''
    sectionInfo.value = ''
    selectedPlan.value = await getPlanFull(planId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function saveTask() {
  if (!selectedPlan.value || !taskContent.value.trim()) return
  const planId = selectedPlan.value.id
  const minutes = Math.max(0, Number(taskMinutes.value) || 0)
  if (!editingTaskId.value && taskSectionIndex.value === null) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (editingTaskId.value) {
      await updatePlanTask(planId, editingTaskId.value, taskContent.value.trim(), minutes)
    } else if (taskSectionIndex.value !== null) {
      await addPlanTask(planId, taskSectionIndex.value, taskContent.value.trim(), minutes)
    }
    taskContent.value = ''
    taskMinutes.value = 30
    taskSectionIndex.value = null
    editingTaskId.value = null
    editingTaskSectionIndex.value = null
    selectedPlan.value = await getPlanFull(planId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

function startTaskEdit(sectionIndex: number, task: PlanFull['sections'][number]['tasks'][number]) {
  taskSectionIndex.value = null
  editingTaskId.value = task.internal_id
  editingTaskSectionIndex.value = sectionIndex
  taskContent.value = task.content
  taskMinutes.value = task.time_minutes
}

function cancelTaskEdit() {
  taskSectionIndex.value = null
  editingTaskId.value = null
  editingTaskSectionIndex.value = null
  taskContent.value = ''
  taskMinutes.value = 30
}

async function completeTask(taskId: string) {
  if (!selectedPlan.value) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await completePlanTask(planId, taskId)
    selectedPlan.value = await getPlanFull(planId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function deleteTask(taskId: string) {
  if (!selectedPlan.value || !confirm(`${t('plans.delete')}?`)) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await deletePlanTask(planId, taskId)
    selectedPlan.value = await getPlanFull(planId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

function backFromDetail() {
  selectedPlan.value = null
  editingMeta.value = false
  view.value = 'events'
  loadPlans()
}

const activeTaskCount = computed(() => selectedPlan.value?.sections.reduce((total, section) => total + section.tasks.length, 0) || 0)

onMounted(loadPlans)
</script>

<template>
  <div class="plans-hub">
    <header class="plans-header">
      <button class="plans-back" @click="AudioManager.playSound('click'); router.push('/')" :aria-label="t('plans.back')">
        <ArrowLeft :size="18" />
      </button>
      <div>
        <p class="plans-eyebrow">{{ t('plans.center') }}</p>
        <h1>{{ view === 'detail' ? selectedPlan?.name : t('plans.center') }}</h1>
      </div>
      <button v-if="view === 'events'" class="plans-primary" @click="showCreate = true"><Plus :size="16" /> {{ t('plans.create') }}</button>
    </header>

    <main class="plans-content">
      <template v-if="view === 'hub'">
        <section class="plan-domain-grid">
          <button class="domain-card theme-card" @click="router.push('/plan')">
            <Clock3 :size="28" />
            <strong>{{ t('plans.time') }}</strong>
            <span>{{ t('plans.timeDescription') }}</span>
            <ChevronRight :size="18" />
          </button>
          <button class="domain-card theme-card" @click="openEvents">
            <ClipboardList :size="28" />
            <strong>{{ t('plans.events') }}</strong>
            <span>{{ t('plans.eventsDescription') }}</span>
            <ChevronRight :size="18" />
          </button>
        </section>
      </template>

      <template v-else-if="view === 'events'">
        <p v-if="errorMessage" class="plans-error">{{ errorMessage }}</p>
        <section v-if="isLoading" class="plans-empty theme-card">{{ t('plans.loading') }}</section>
        <section v-else-if="plans.length === 0" class="plans-empty theme-card">
          <FolderPlus :size="34" />
          <strong>{{ t('plans.empty') }}</strong>
          <span>{{ t('plans.emptyHint') }}</span>
          <button class="plans-primary" @click="showCreate = true"><Plus :size="16" /> {{ t('plans.create') }}</button>
        </section>
        <section v-else class="event-plan-grid">
          <button v-for="plan in plans" :key="plan.id" class="event-plan-card theme-card" @click="openPlan(plan)">
            <div class="event-plan-card-top"><span>#{{ plan.id }}</span><ChevronRight :size="17" /></div>
            <strong>{{ plan.name }}</strong>
            <span>{{ formatPlanDate(plan.date) }}</span>
            <small>{{ plan.total_tasks || 0 }} {{ t('tasks.completed') }}</small>
          </button>
        </section>
        <section class="archives-panel theme-card">
          <header><div><h2>{{ t('plans.archived') }}</h2><p>{{ t('plans.archivedAt') }}</p></div></header>
          <p v-if="archives.length === 0" class="section-empty">{{ t('plans.noArchives') }}</p>
          <div v-for="archive in archives" :key="archive.file" class="archive-row">
            <div><strong>{{ archive.name || archive.file }}</strong><span>{{ formatPlanDate(archive.date) }}</span></div>
            <button class="plans-secondary" :disabled="isLoading" @click="restoreArchive(archive)">{{ t('plans.restore') }}</button>
          </div>
        </section>
      </template>

      <template v-else-if="selectedPlan">
        <div v-if="errorMessage" class="plans-error">{{ errorMessage }}</div>
        <div class="detail-toolbar">
          <button class="plans-link" @click="backFromDetail">← {{ t('plans.back') }}</button>
          <div class="detail-actions">
            <button class="plans-secondary" @click="startMetaEdit"><Pencil :size="15" /> {{ t('plans.edit') }}</button>
            <button class="plans-secondary" :disabled="isLoading" @click="archiveSelectedPlan">{{ t('plans.archive') }}</button>
          </div>
        </div>
        <section v-if="editingMeta" class="meta-editor theme-card">
          <label>{{ t('plans.name') }}<input v-model="planName" /></label>
          <label>{{ t('plans.date') }}<input v-model="planDate" type="date" /></label>
          <div><button class="plans-secondary" @click="editingMeta = false">{{ t('plans.cancel') }}</button><button class="plans-primary" @click="savePlanMeta">{{ t('plans.save') }}</button></div>
        </section>
        <section class="plan-detail-summary theme-card">
          <div><span>{{ t('plans.date') }}</span><strong>{{ formatPlanDate(selectedPlan.date) }}</strong></div>
          <div><span>{{ t('plans.events') }}</span><strong>{{ activeTaskCount }}</strong></div>
          <div><span>{{ t('plans.completed') }}</span><strong>{{ selectedPlan.sections.reduce((n, section) => n + section.tasks.filter((task) => task.finish).length, 0) }}</strong></div>
        </section>
        <section class="section-editor theme-card">
          <input v-model="sectionName" :placeholder="t('plans.sectionName')" />
          <input v-model="sectionInfo" :placeholder="t('plans.sectionInfo')" />
          <button class="plans-secondary" :disabled="isLoading" @click="saveSection"><Plus :size="15" /> {{ t('plans.addSection') }}</button>
        </section>
        <section v-if="selectedPlan.sections.length === 0" class="plans-empty theme-card">{{ t('plans.noSections') }}</section>
        <section v-for="section in selectedPlan.sections" :key="section.index" class="plan-section theme-card">
          <header><div><span class="section-letter">{{ section.letter }}</span><strong>{{ section.name }}</strong><small>{{ section.info }}</small></div><button class="plans-secondary" :disabled="isLoading" @click="taskSectionIndex = section.index"><Plus :size="15" /> {{ t('plans.addTask') }}</button></header>
          <div v-if="taskSectionIndex === section.index || editingTaskSectionIndex === section.index" class="task-editor">
            <label>{{ t('plans.taskContent') }}<input v-model="taskContent" autofocus /></label>
            <label>{{ t('plans.taskMinutes') }}<input v-model.number="taskMinutes" type="number" min="0" step="1" /></label>
            <button class="plans-secondary" @click="cancelTaskEdit">{{ t('plans.cancel') }}</button>
            <button class="plans-primary" @click="saveTask">{{ editingTaskId ? t('plans.editTask') : t('plans.save') }}</button>
          </div>
          <p v-if="section.tasks.length === 0" class="section-empty">{{ t('plans.noTasks') }}</p>
          <article v-for="task in section.tasks" :key="task.internal_id" class="event-task-row" :class="{ finished: task.finish }">
            <button class="task-complete" :disabled="!!task.finish || isLoading" :aria-label="t('plans.complete')" @click="completeTask(task.internal_id)"><Check v-if="task.finish" :size="15" /></button>
            <div><strong>{{ task.display_id }}</strong><span>{{ task.content }}</span></div>
            <small>{{ task.time_minutes }} min</small>
            <button class="task-edit" :disabled="isLoading" :aria-label="t('plans.editTask')" @click="startTaskEdit(section.index, task)"><Pencil :size="15" /></button>
            <button class="task-delete" :disabled="isLoading" :aria-label="t('plans.delete')" @click="deleteTask(task.internal_id)"><Trash2 :size="15" /></button>
          </article>
          <div v-if="Object.keys(section.groups).length" class="group-list"><span v-for="(group, key) in section.groups" :key="key">{{ key }} · {{ group.title }}</span></div>
        </section>
      </template>
    </main>

    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate = false">
      <form class="create-modal theme-card" @submit.prevent="createPlan" @keydown.esc="showCreate = false">
        <h2>{{ t('plans.create') }}</h2>
        <p>{{ t('plans.createHint') }}</p>
        <label>{{ t('plans.name') }}<input v-model="planName" required autofocus /></label>
        <label>{{ t('plans.date') }}<input v-model="planDate" type="date" required /></label>
        <div class="modal-actions"><button type="button" class="plans-secondary" @click="showCreate = false">{{ t('plans.cancel') }}</button><button class="plans-primary" type="submit" :disabled="isLoading">{{ t('plans.create') }}</button></div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.plans-hub { min-height: 100vh; color: var(--color-text-primary); background: var(--color-bg); }
.plans-header { display: flex; align-items: center; gap: 15px; max-width: 1080px; margin: 0 auto; padding: 30px 28px 20px; }
.plans-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.plans-eyebrow { margin: 0 0 4px; color: var(--color-text-tertiary); font-size: 12px; letter-spacing: .08em; }
.plans-header h1 { margin: 0; font-size: 25px; }
.plans-primary, .plans-secondary, .plans-link { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; padding: 8px 12px; cursor: pointer; font-weight: 600; }
.plans-primary { margin-left: auto; border: 1px solid var(--color-primary); color: var(--color-button-text); background: var(--color-primary); }
.plans-secondary { border: 1px solid var(--color-border); color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.plans-link { border: 0; padding-left: 0; color: var(--color-primary); background: transparent; }
.plans-content { max-width: 1080px; margin: 0 auto; padding: 10px 28px 50px; }
.plan-domain-grid, .event-plan-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.domain-card, .event-plan-card { position: relative; display: grid; gap: 9px; border: 1px solid var(--color-border); border-radius: 17px; padding: 24px; color: var(--color-text-primary); background: var(--color-bg-secondary); text-align: left; cursor: pointer; transition: border-color .18s, transform .18s; }
.domain-card:hover, .event-plan-card:hover { border-color: var(--color-border-hover); transform: translateY(-2px); }
.domain-card svg { color: var(--color-primary); }
.domain-card strong, .event-plan-card strong { font-size: 18px; }
.domain-card span, .event-plan-card span, .event-plan-card small { color: var(--color-text-secondary); }
.domain-card > svg:last-child { position: absolute; right: 20px; bottom: 20px; color: var(--color-text-tertiary); }
.event-plan-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.event-plan-card-top { display: flex; justify-content: space-between; color: var(--color-text-tertiary); font-size: 12px; }
.event-plan-card-top svg { color: var(--color-text-tertiary); }
.plans-empty { display: grid; place-items: center; gap: 10px; min-height: 230px; border: 1px dashed var(--color-border); border-radius: 17px; color: var(--color-text-tertiary); text-align: center; }
.plans-empty strong { color: var(--color-text-secondary); }
.plans-error { margin-bottom: 14px; color: var(--color-error); font-size: 13px; }
.detail-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.detail-actions { display: flex; gap: 8px; }
.meta-editor, .section-editor { display: flex; align-items: flex-end; gap: 10px; margin-bottom: 14px; padding: 14px; border: 1px solid var(--color-border); border-radius: 14px; }
.meta-editor label, .section-editor label, .task-editor label, .create-modal label { display: grid; gap: 6px; color: var(--color-text-secondary); font-size: 12px; }
.meta-editor input, .section-editor input, .task-editor input, .create-modal input { min-width: 0; border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 10px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.meta-editor input:focus, .section-editor input:focus, .task-editor input:focus, .create-modal input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.plan-detail-summary { display: flex; gap: 38px; margin-bottom: 14px; padding: 17px 20px; border: 1px solid var(--color-border); border-radius: 14px; }
.plan-detail-summary div { display: grid; gap: 4px; }
.plan-detail-summary span { color: var(--color-text-tertiary); font-size: 12px; }
.section-editor { align-items: center; }
.section-editor input:first-child { flex: 1; }
.section-editor input:nth-child(2) { flex: 1.5; }
.plan-section { margin-bottom: 12px; padding: 17px; border: 1px solid var(--color-border); border-radius: 14px; }
.plan-section > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.plan-section > header > div { display: flex; align-items: center; gap: 9px; min-width: 0; }
.section-letter { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 8px; color: var(--color-button-text); background: var(--color-primary); font-size: 12px; font-weight: 700; }
.plan-section header small { overflow: hidden; color: var(--color-text-tertiary); text-overflow: ellipsis; white-space: nowrap; }
.task-editor { display: flex; align-items: flex-end; gap: 9px; margin: 15px 0 8px; padding: 10px; border-radius: 10px; background: var(--color-bg-secondary); }
.task-editor label:first-child { flex: 1; }
.section-empty { color: var(--color-text-tertiary); font-size: 13px; }
.event-task-row { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto 28px 28px; align-items: center; gap: 10px; padding: 12px 0; border-top: 1px solid var(--color-border); }
.event-task-row > div { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
.event-task-row > div strong { color: var(--color-primary); font-size: 12px; }
.event-task-row > div span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-task-row > small { color: var(--color-text-tertiary); white-space: nowrap; }
.event-task-row.finished { opacity: .62; }
.event-task-row.finished span { text-decoration: line-through; }
.task-complete, .task-edit, .task-delete { display: grid; place-items: center; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.task-complete { width: 22px; height: 22px; border: 2px solid var(--color-border-hover); border-radius: 50%; }
.task-complete:disabled { color: var(--color-button-text); background: var(--color-primary); }
.group-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.group-list span { padding: 4px 7px; border-radius: 6px; color: var(--color-text-tertiary); background: var(--color-bg-secondary); font-size: 11px; }
.archives-panel { margin-top: 24px; padding: 17px; border: 1px solid var(--color-border); border-radius: 14px; }
.archives-panel header h2, .archives-panel header p { margin: 0; }
.archives-panel header p { margin-top: 4px; color: var(--color-text-tertiary); font-size: 12px; }
.archive-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 0; border-top: 1px solid var(--color-border); }
.archive-row > div { display: grid; gap: 4px; min-width: 0; }
.archive-row span { color: var(--color-text-tertiary); font-size: 12px; }
.modal-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; padding: 20px; background: rgba(0,0,0,.3); }
.create-modal { display: grid; gap: 14px; width: min(440px, 100%); padding: 24px; border: 1px solid var(--color-border); border-radius: 18px; background: var(--color-bg); box-shadow: var(--shadow-lg, 0 18px 50px rgba(0,0,0,.2)); }
.create-modal h2, .create-modal p { margin: 0; }
.create-modal p { color: var(--color-text-secondary); font-size: 13px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
@media (prefers-reduced-motion: reduce) { .domain-card, .event-plan-card { transition: none; } }
@media (max-width: 760px) { .plans-header, .plans-content { padding-left: 18px; padding-right: 18px; } .plan-domain-grid, .event-plan-grid { grid-template-columns: 1fr; } .meta-editor, .section-editor, .task-editor { align-items: stretch; flex-direction: column; } .meta-editor > div { display: flex; justify-content: flex-end; } .plan-detail-summary { gap: 18px; justify-content: space-between; } }
</style>
