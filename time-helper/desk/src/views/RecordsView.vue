<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { hoursToHm, isTimeOverlap, getTodayDate } from '@/services/dataService'
import { ArrowLeft, Plus, Pencil, Trash2, X, Check } from 'lucide-vue-next'
import type { TimeRecord } from '@/types'
import { unlinkTodoFromTimeRecord } from '@/services/workspaceSync'
import { TodoService, type UnifiedTodo } from '@/services/todoService'
import { useI18n } from '@/i18n'
import { notifyToast } from '@/services/toastService'
import { requestConfirm } from '@/services/confirmService'
import { onWorkspaceChanged } from '@/services/workspaceEvents'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const { t, locale } = useI18n()

const records = computed(() => appStore.todayRecords)
const todayPlan = computed(() => appStore.todayPlan)
const plans = computed(() => appStore.plans)
const todos = ref<UnifiedTodo[]>([])
const todoOptionsUnavailable = ref(false)
const todoOptionsLoaded = ref(false)
const selectedTodoId = ref('')
const todoOptions = computed(() => {
  const selected = todos.value.find((todo) => todo.id === selectedTodoId.value)
  const active = todos.value.filter((todo) => !['archived', 'cancelled'].includes(todo.status))
  return selected && !active.some((todo) => todo.id === selected.id) ? [selected, ...active] : active
})
const todoTitleById = computed(() => new Map(todos.value.map((todo) => [todo.id, todo.title])))
const linkedTodoFromQuery = computed(() => {
  const value = route.query.todo
  return typeof value === 'string' ? value : ''
})

async function loadTodoOptions(): Promise<void> {
  try {
    todos.value = await TodoService.list()
    todoOptionsUnavailable.value = false
    todoOptionsLoaded.value = true
  } catch {
    todos.value = []
    todoOptionsUnavailable.value = true
    todoOptionsLoaded.value = false
  }
}

let stopWorkspaceListener: (() => void) | null = null

function openLinkedTodo(todoId: string) {
  if (todoOptionsLoaded.value && !todoTitleById.value.has(todoId)) return
  router.push({ path: '/tasks', query: { todo: todoId } })
}

function isLinkedTodoUnavailable(todoId: string): boolean {
  return todoOptionsLoaded.value && !todoTitleById.value.has(todoId)
}

function preselectLinkedTodo(): void {
  const todoId = linkedTodoFromQuery.value
  if (!todoId || !todos.value.some((todo) => todo.id === todoId)) return
  openAddForm()
  selectedTodoId.value = linkedTodoFromQuery.value
}

// 获取当前计划的标签列表
const availableTags = computed(() => {
  const plan = plans.value[todayPlan.value.name]
  return plan?.items.map(item => item.name) || []
})

// 编辑状态
const isEditing = ref(false)
const editingIndex = ref(-1)
const showForm = ref(false)
const isSaving = ref(false)

// 表单数据
const formMode = ref<'time' | 'duration'>('time')
const formStart = ref({ h: '09', m: '00' })
const formEnd = ref({ h: '10', m: '00' })
const formDuration = ref({ h: '1', m: '0' })
const formDurationRef = ref<'start' | 'end'>('start')
const formDurationTime = ref({ h: '09', m: '00' })
const formContent = ref('')
const formTag = ref('')

// 重置表单
function resetForm() {
  formMode.value = 'time'
  formStart.value = { h: '09', m: '00' }
  formEnd.value = { h: '10', m: '00' }
  formDuration.value = { h: '1', m: '0' }
  formDurationRef.value = 'start'
  formDurationTime.value = { h: '09', m: '00' }
  formContent.value = ''
  formTag.value = availableTags.value[0] || ''
  selectedTodoId.value = ''
  isEditing.value = false
  editingIndex.value = -1
}

// 打开新增表单
function openAddForm() {
  resetForm()
  formTag.value = availableTags.value[0] || ''
  showForm.value = true
}

// 打开编辑表单
function openEditForm(index: number) {
  const record = records.value[index]
  if (!record) return

  const [sh, sm] = record.start.split(':')
  const [eh, em] = record.end.split(':')

  formStart.value = { h: sh, m: sm }
  formEnd.value = { h: eh, m: em }
  formContent.value = record.content
  formTag.value = record.tag
  selectedTodoId.value = record.todo_id || ''
  isEditing.value = true
  editingIndex.value = index
  showForm.value = true
}

// 检查时间冲突
function checkConflict(start: string, end: string, tag: string, excludeIndex = -1): string | null {
  const plan = plans.value[todayPlan.value.name]
  const planType = plan?.plan_type || '切分制'

  for (let i = 0; i < records.value.length; i++) {
    if (i === excludeIndex) continue
    const r = records.value[i]

    if (planType === '切分制') {
      if (isTimeOverlap(start, end, r.start, r.end)) {
        return t('records.validation.conflictWith', { tag: r.tag, start: r.start, end: r.end })
      }
    } else {
      if (r.tag === tag && isTimeOverlap(start, end, r.start, r.end)) {
        return t('records.validation.conflictWith', { tag: r.tag, start: r.start, end: r.end })
      }
    }
  }
  return null
}

// 保存记录
async function saveRecord() {
  if (isSaving.value) return
  isSaving.value = true
  try {
    await saveRecordInternal()
  } finally {
    isSaving.value = false
  }
}

async function saveRecordInternal() {
  // 验证内容
  if (!formContent.value.trim()) {
    notifyToast(t('records.validation.content'), 'error')
    return
  }

  // 验证标签
  if (!formTag.value.trim()) {
    notifyToast(t('records.validation.tag'), 'error')
    return
  }

  let start: string, end: string
  let startMinutes: number, endMinutes: number

  if (formMode.value === 'time') {
    // 解析并验证时间
    const sh = parseInt(String(formStart.value.h)) || 0
    const sm = parseInt(String(formStart.value.m)) || 0
    const eh = parseInt(String(formEnd.value.h)) || 0
    const em = parseInt(String(formEnd.value.m)) || 0

    // 验证小时范围
    if (sh < 0 || sh > 23 || eh < 0 || eh > 23) {
      notifyToast(t('records.validation.hour'), 'error')
      return
    }
    // 验证分钟范围
    if (sm < 0 || sm > 59 || em < 0 || em > 59) {
      notifyToast(t('records.validation.minute'), 'error')
      return
    }

    start = `${String(sh).padStart(2, '0')}:${String(sm).padStart(2, '0')}`
    end = `${String(eh).padStart(2, '0')}:${String(em).padStart(2, '0')}`
    startMinutes = sh * 60 + sm
    endMinutes = eh * 60 + em

    // 验证结束时间必须大于开始时间
    if (endMinutes <= startMinutes) {
      notifyToast(t('records.validation.end'), 'error')
      return
    }
  } else {
    // 时长模式
    const dh = parseInt(formDuration.value.h) || 0
    const dm = parseInt(formDuration.value.m) || 0
    const refH = parseInt(formDurationTime.value.h) || 0
    const refM = parseInt(formDurationTime.value.m) || 0

    // 验证时长
    if (dh === 0 && dm === 0) {
    notifyToast(t('records.validation.durationZero'), 'error')
      return
    }
    if (dh < 0 || dm < 0) {
    notifyToast(t('records.validation.durationNegative'), 'error')
      return
    }
    if (dm > 59) {
    notifyToast(t('records.validation.minute'), 'error')
      return
    }
    // 验证时长不超过 24 小时
    const totalMinutes = dh * 60 + dm
    if (totalMinutes > 24 * 60) {
    notifyToast(t('records.validation.durationMax'), 'error')
      return
    }

    // 验证参考时间
    if (refH < 0 || refH > 23) {
    notifyToast(t('records.validation.hour'), 'error')
      return
    }
    if (refM < 0 || refM > 59) {
    notifyToast(t('records.validation.minute'), 'error')
      return
    }

    const durationHours = dh + dm / 60
    const refMinutes = refH * 60 + refM

    if (formDurationRef.value === 'start') {
      start = `${String(refH).padStart(2, '0')}:${String(refM).padStart(2, '0')}`
      startMinutes = refMinutes
      const endMins = refMinutes + durationHours * 60
      const eh = Math.floor(endMins / 60) % 24
      const em = Math.floor(endMins % 60)
      end = `${String(eh).padStart(2, '0')}:${String(em).padStart(2, '0')}`
      endMinutes = endMins % (24 * 60)
    } else {
      end = `${String(refH).padStart(2, '0')}:${String(refM).padStart(2, '0')}`
      endMinutes = refMinutes
      const startMins = refMinutes - durationHours * 60
      const sh = Math.floor((startMins + 24 * 60) / 60) % 24
      const sm = Math.floor(((startMins + 24 * 60) % 60))
      start = `${String(sh).padStart(2, '0')}:${String(sm).padStart(2, '0')}`
      startMinutes = (startMins + 24 * 60) % (24 * 60)
    }
  }

  // 检查冲突
  const conflict = checkConflict(start, end, formTag.value, editingIndex.value)
  if (conflict) {
    notifyToast(t('records.validation.conflict') + conflict, 'error')
    return
  }

  const duration = (endMinutes - startMinutes) / 60
  const originalRecord = isEditing.value ? records.value[editingIndex.value] : undefined

  const record: TimeRecord = {
    id: originalRecord?.id || `TR-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    todo_id: selectedTodoId.value || undefined,
    date: getTodayDate(),
    start,
    end,
    duration,
    content: formContent.value.trim(),
    tag: formTag.value
  }

  if (isEditing.value) {
    await appStore.updateRecord(editingIndex.value, record)
  } else {
    await appStore.addRecord(record)
  }
  let todoLinkFailed = false
  if (originalRecord?.todo_id && originalRecord.todo_id !== record.todo_id) {
    try {
      await unlinkTodoFromTimeRecord({ ...record, todo_id: originalRecord.todo_id })
    } catch (error) {
      todoLinkFailed = true
      console.warn('Failed to unlink previous todo record reference', error)
    }
  }
  if (record.todo_id) {
    try {
      const todo = todos.value.find((item) => item.id === record.todo_id)
      if (todo && !todo.related_time_record_ids?.includes(record.id as string)) {
        const updated = await TodoService.update(todo.id, {
          related_time_record_ids: [...(todo.related_time_record_ids || []), record.id as string],
        })
        todos.value = todos.value.map((item) => item.id === updated.id ? updated : item)
      }
    } catch (error) {
      todoLinkFailed = true
      console.warn('Failed to link saved record to todo', error)
    }
  }
  notifyToast(todoLinkFailed ? t('records.todoLinkFailed') : t('records.saved'), todoLinkFailed ? 'error' : 'success')

  showForm.value = false
  resetForm()
}

// 删除记录
async function deleteRecord(index: number) {
  if (!(await requestConfirm(t('records.deleteConfirm'), { tone: 'danger' }))) return
  const record = records.value[index]
  await appStore.deleteRecord(index)
  if (record) {
    try { await unlinkTodoFromTimeRecord(record) } catch (error) { console.warn('Failed to clean deleted record link', error) }
  }
}

onMounted(async () => {
  formTag.value = availableTags.value[0] || ''
  stopWorkspaceListener = onWorkspaceChanged((source) => {
    if (source === 'todos' || source === 'archive') void loadTodoOptions()
    if (source === 'records' || source === 'plans' || source === 'settings' || source === 'archive') {
      void appStore.refreshWorkspaceData().catch((error) => {
        console.warn('Failed to refresh records workspace after external change:', error)
      })
    }
  })
  await loadTodoOptions()
  // A task with no existing record opens the record form with its relation
  // preselected, completing the task -> time-record workflow.
  preselectLinkedTodo()
})

watch(linkedTodoFromQuery, () => {
  if (todos.value.length > 0) preselectLinkedTodo()
})

onUnmounted(() => {
  stopWorkspaceListener?.()
  stopWorkspaceListener = null
})
</script>

<template>
  <div class="records-view">
    <header class="header">
      <button type="button" class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="16" />
        <span>{{ t('records.back') }}</span>
      </button>
      <h1>{{ t('records.title') }}</h1>
      <button type="button" class="add-btn" @click="openAddForm">
        <Plus :size="16" />
        <span>{{ t('records.add') }}</span>
      </button>
    </header>

    <main class="main-content">
      <!-- 记录列表 -->
      <div class="records-list" v-if="records.length > 0">
        <div
          v-for="(record, index) in records"
          :key="index"
          class="record-item"
        >
          <div class="record-info">
            <span class="record-tag">[{{ record.tag }}]</span>
            <span class="record-time">{{ record.start }} - {{ record.end }}</span>
            <span class="record-duration">({{ hoursToHm(record.duration, locale) }})</span>
          </div>
          <div class="record-content">{{ record.content }}</div>
          <button
            v-if="record.todo_id"
            type="button"
            class="record-todo-link"
            :class="{ unavailable: isLinkedTodoUnavailable(record.todo_id) }"
            :disabled="isLinkedTodoUnavailable(record.todo_id)"
            :title="isLinkedTodoUnavailable(record.todo_id) ? t('records.todoUnavailable') : t('records.openTodo')"
            @click="openLinkedTodo(record.todo_id)"
          >
            {{ isLinkedTodoUnavailable(record.todo_id) ? t('records.todoUnavailable') : `${t('records.linkedTodo')}: ${todoTitleById.get(record.todo_id) || record.todo_id}` }}
          </button>
          <div class="record-actions">
            <button type="button" class="icon-btn" :aria-label="t('records.edit')" @click="openEditForm(index)" :title="t('records.edit')">
              <Pencil :size="14" />
            </button>
            <button type="button" class="icon-btn danger" :aria-label="t('records.delete')" @click="deleteRecord(index)" :title="t('records.delete')">
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-else>
        <p>{{ t('records.empty') }}</p>
        <p class="hint">{{ t('records.emptyHint') }}</p>
      </div>
    </main>

    <!-- 表单弹窗 -->
    <div class="modal-overlay" v-if="showForm" @click.self="showForm = false">
      <div class="modal" @keydown.esc="showForm = false">
        <form class="modal-form" @submit.prevent="saveRecord">
        <div class="modal-header">
          <h2>{{ isEditing ? t('records.edit') : t('records.add') }}</h2>
          <button type="button" class="close-btn" :aria-label="t('search.close')" @click="showForm = false">
            <X :size="20" />
          </button>
        </div>

        <div class="modal-body">
          <!-- 输入模式切换 -->
          <div class="mode-switch">
            <button
              type="button"
              :class="['mode-btn', { active: formMode === 'time' }]"
              @click="formMode = 'time'"
            >
              {{ t('records.modeTime') }}
            </button>
            <button
              type="button"
              :class="['mode-btn', { active: formMode === 'duration' }]"
              @click="formMode = 'duration'"
            >
              {{ t('records.modeDuration') }}
            </button>
          </div>

          <!-- 时间模式 -->
          <div class="form-section" v-if="formMode === 'time'">
            <div class="time-input-row">
              <label>{{ t('records.start') }}：</label>
              <input type="number" v-model="formStart.h" min="0" max="23" class="time-input" />
              <span>:</span>
              <input type="number" v-model="formStart.m" min="0" max="59" class="time-input" />
            </div>
            <div class="time-input-row">
              <label>{{ t('records.end') }}：</label>
              <input type="number" v-model="formEnd.h" min="0" max="23" class="time-input" />
              <span>:</span>
              <input type="number" v-model="formEnd.m" min="0" max="59" class="time-input" />
            </div>
          </div>

          <!-- 时长模式 -->
          <div class="form-section" v-else>
            <div class="time-input-row">
              <label>{{ t('records.duration') }}：</label>
              <input type="number" v-model="formDuration.h" min="0" class="time-input small" />
              <span>{{ t('records.hours') }}</span>
              <input type="number" v-model="formDuration.m" min="0" max="59" class="time-input small" />
              <span>{{ t('records.minutes') }}</span>
            </div>
            <div class="time-input-row">
              <label>{{ t('records.referenceTime') }}：</label>
              <input type="number" v-model="formDurationTime.h" min="0" max="23" class="time-input" />
              <span>:</span>
              <input type="number" v-model="formDurationTime.m" min="0" max="59" class="time-input" />
            </div>
            <div class="radio-group">
              <label>
                <input type="radio" v-model="formDurationRef" value="start" />
                <span>{{ t('records.referenceStart') }}</span>
              </label>
              <label>
                <input type="radio" v-model="formDurationRef" value="end" />
                <span>{{ t('records.referenceEnd') }}</span>
              </label>
            </div>
          </div>

          <!-- 内容 -->
          <div class="form-section">
            <label>{{ t('records.content') }}：</label>
            <input
              type="text"
              v-model="formContent"
              :placeholder="t('records.contentPlaceholder')"
              class="text-input"
            />
          </div>

          <!-- 标签 -->
          <div class="form-section">
            <label>{{ t('records.category') }}：</label>
            <select v-model="formTag" class="select-input">
              <option v-for="tag in availableTags" :key="tag" :value="tag">{{ tag }}</option>
            </select>
          </div>

          <div class="form-section">
            <label>{{ t('records.linkTodo') }}：</label>
            <select v-model="selectedTodoId" class="select-input" :disabled="todoOptionsUnavailable">
              <option value="">{{ t('records.noLinkedTodo') }}</option>
              <option v-for="todo in todoOptions" :key="todo.id" :value="todo.id">{{ todo.title }}</option>
            </select>
            <p v-if="todoOptionsUnavailable" class="todo-options-unavailable" role="status" aria-live="polite">
              <span>{{ t('records.todoOptionsUnavailable') }}</span>
              <button type="button" @click="loadTodoOptions">{{ t('records.retryTodoOptions') }}</button>
            </p>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn secondary" @click="showForm = false">{{ t('records.cancel') }}</button>
          <button type="submit" class="btn primary" :disabled="isSaving">
            <Check :size="16" />
            <span>{{ t('records.save') }}</span>
          </button>
        </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.records-view {
  min-height: 100vh;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.back-btn, .add-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover, .add-btn:hover {
  background: var(--color-bg-tertiary);
}

.add-btn {
  margin-left: auto;
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.add-btn:hover {
  background: var(--color-primary-hover);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.record-item {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  transition: all var(--transition-fast);
}

.record-item:hover {
  border-color: var(--color-border-hover);
}

.record-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.record-tag {
  font-weight: 600;
  color: var(--color-primary);
}

.record-time {
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
}

.record-duration {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.record-content {
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}
.todo-options-unavailable { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 6px 0 0; color: var(--color-text-tertiary); font-size: 11px; }
.todo-options-unavailable button { flex: 0 0 auto; border: 1px solid var(--color-border); border-radius: 7px; padding: 5px 8px; color: var(--color-primary); background: var(--color-bg-secondary); cursor: pointer; font: inherit; font-weight: 650; }
.todo-options-unavailable button:hover, .todo-options-unavailable button:focus-visible { border-color: var(--color-primary); outline: 0; }

.record-todo-link {
  display: inline-block;
  margin-bottom: var(--spacing-sm);
  border: 0;
  padding: 0;
  font: inherit;
  text-align: left;
  cursor: pointer;
  background: transparent;
  color: var(--color-primary);
  font-size: 0.75rem;
}
.record-todo-link:hover { text-decoration: underline; }

.record-actions {
  display: flex;
  gap: var(--spacing-xs);
  justify-content: flex-end;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.icon-btn.danger:hover {
  background: var(--color-error);
  border-color: var(--color-error);
  color: white;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-tertiary);
}

.empty-state .hint {
  font-size: 0.875rem;
  margin-top: var(--spacing-sm);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn var(--transition-fast);
}

.modal {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  box-sizing: border-box;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp var(--transition-normal);
}

.modal-form {
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
}

.form-section {
  margin-bottom: var(--spacing-lg);
}

.form-section label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.mode-switch {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.mode-btn {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.time-input-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.time-input-row label {
  width: 80px;
  margin-bottom: 0;
}

.time-input {
  width: 60px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  text-align: center;
  font-family: var(--font-mono);
}

.time-input.small {
  width: 50px;
}

.time-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.radio-group {
  display: flex;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-sm);
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  margin-bottom: 0;
}

.text-input, .select-input {
  width: 100%;
  box-sizing: border-box;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 1rem;
}

.text-input:focus, .select-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--transition-fast);
}

.btn.secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.btn.secondary:hover {
  background: var(--color-bg-tertiary);
}

.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.btn.primary:hover {
  background: var(--color-primary-hover);
}

/* Desktop uses the available workbench width; the compact single-column
   layout remains the default for phones and narrow windows. */
@media (min-width: 1100px) {
  .main-content { max-width: 1180px; }
  .records-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: start; }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@media (max-width: 680px) {
  .records-view { padding: 16px; }
  .header { flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
  .header h1 { order: 3; flex-basis: 100%; font-size: 1.25rem; }
  .back-btn, .add-btn { min-height: 40px; }
  .add-btn { margin-left: auto; }
  .record-item { padding: 13px; }
  .modal-footer { flex-direction: column-reverse; }
  .modal-footer .btn { justify-content: center; min-height: 42px; }
}
</style>
