<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { AudioManager } from '@/audio'
import {
  hoursToHm, isTimeOverlap, getTodayDate,
  rgbToHex, autoBalance
} from '@/services/dataService'
import {
  ArrowLeft, Plus, Pencil, Trash2, X, Check,
  Calendar, FolderKanban, RefreshCw, ClipboardList,
  Clock, ChevronRight
} from 'lucide-vue-next'
import type { TimeRecord, PlanItem, ScheduleRule } from '@/types'
import EmptyState from '@/components/EmptyState.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { useI18n } from '@/i18n'
import { unlinkTodoFromTimeRecord } from '@/services/workspaceSync'
import { notifyToast } from '@/services/toastService'

const router = useRouter()
const appStore = useAppStore()
const { t } = useI18n()

// ============ Records 相关状态 ============
const records = computed(() => appStore.todayRecords)
const todayPlan = computed(() => appStore.todayPlan)
const plans = computed(() => appStore.plans)
const scheduleRules = computed(() => appStore.scheduleRules)

const availableTags = computed(() => {
  const plan = plans.value[todayPlan.value.name]
  return plan?.items.map(item => item.name) || []
})

// 记录编辑状态
const isEditing = ref(false)
const editingIndex = ref(-1)
const showRecordForm = ref(false)

const formMode = ref<'time' | 'duration'>('time')
const formStart = ref({ h: '09', m: '00' })
const formEnd = ref({ h: '10', m: '00' })
const formDuration = ref({ h: '1', m: '0' })
const formDurationRef = ref<'start' | 'end'>('start')
const formDurationTime = ref({ h: '09', m: '00' })
const formContent = ref('')
const formTag = ref('')

function resetRecordForm() {
  formMode.value = 'time'
  formStart.value = { h: '09', m: '00' }
  formEnd.value = { h: '10', m: '00' }
  formDuration.value = { h: '1', m: '0' }
  formDurationRef.value = 'start'
  formDurationTime.value = { h: '09', m: '00' }
  formContent.value = ''
  formTag.value = availableTags.value[0] || ''
  isEditing.value = false
  editingIndex.value = -1
}

function openAddForm() {
  resetRecordForm()
  formTag.value = availableTags.value[0] || ''
  showRecordForm.value = true
}

function openEditForm(index: number) {
  const record = records.value[index]
  if (!record) return
  const [sh, sm] = record.start.split(':')
  const [eh, em] = record.end.split(':')
  formStart.value = { h: sh, m: sm }
  formEnd.value = { h: eh, m: em }
  formContent.value = record.content
  formTag.value = record.tag
  isEditing.value = true
  editingIndex.value = index
  showRecordForm.value = true
}

function checkConflict(start: string, end: string, tag: string, excludeIndex = -1): string | null {
  const plan = plans.value[todayPlan.value.name]
  const planType = plan?.plan_type || '切分制'
  for (let i = 0; i < records.value.length; i++) {
    if (i === excludeIndex) continue
    const r = records.value[i]
    if (planType === '切分制') {
      if (isTimeOverlap(start, end, r.start, r.end)) {
        return `${t('legacyPlan.conflict')}[${r.tag}] ${r.start}-${r.end}`
      }
    } else {
      if (r.tag === tag && isTimeOverlap(start, end, r.start, r.end)) {
        return `${t('legacyPlan.conflict')}[${r.tag}] ${r.start}-${r.end}`
      }
    }
  }
  return null
}

async function saveRecord() {
  // 使用表单验证
  const valid = recordValidation.validate({
    content: formContent.value,
    tag: formTag.value,
  })
  if (!valid) return

  let start: string, end: string
  let startMinutes: number, endMinutes: number

  if (formMode.value === 'time') {
    const sh = parseInt(String(formStart.value.h)) || 0
    const sm = parseInt(String(formStart.value.m)) || 0
    const eh = parseInt(String(formEnd.value.h)) || 0
    const em = parseInt(String(formEnd.value.m)) || 0
    if (sh < 0 || sh > 23 || eh < 0 || eh > 23) { notifyToast(t('legacyPlan.validationHour'), 'error'); return }
    if (sm < 0 || sm > 59 || em < 0 || em > 59) { notifyToast(t('legacyPlan.validationMinute'), 'error'); return }
    start = `${String(sh).padStart(2, '0')}:${String(sm).padStart(2, '0')}`
    end = `${String(eh).padStart(2, '0')}:${String(em).padStart(2, '0')}`
    startMinutes = sh * 60 + sm
    endMinutes = eh * 60 + em
  if (endMinutes <= startMinutes) { notifyToast(t('legacyPlan.validationEnd'), 'error'); return }
  } else {
    const dh = parseInt(formDuration.value.h) || 0
    const dm = parseInt(formDuration.value.m) || 0
    const refH = parseInt(formDurationTime.value.h) || 0
    const refM = parseInt(formDurationTime.value.m) || 0
  if (dh === 0 && dm === 0) { notifyToast(t('legacyPlan.validationDurationZero'), 'error'); return }
  if (dh < 0 || dm < 0) { notifyToast(t('legacyPlan.validationDurationNegative'), 'error'); return }
  if (dm > 59) { notifyToast(t('legacyPlan.validationMinute'), 'error'); return }
    const totalMinutes = dh * 60 + dm
  if (totalMinutes > 24 * 60) { notifyToast(t('legacyPlan.validationDurationMax'), 'error'); return }
  if (refH < 0 || refH > 23) { notifyToast(t('legacyPlan.validationHour'), 'error'); return }
  if (refM < 0 || refM > 59) { notifyToast(t('legacyPlan.validationMinute'), 'error'); return }
    const durationHours = dh + dm / 60
    const refMinutes = refH * 60 + refM
    if (formDurationRef.value === 'start') {
      start = `${String(refH).padStart(2, '0')}:${String(refM).padStart(2, '0')}`
      startMinutes = refMinutes
      const endMins = refMinutes + durationHours * 60
      const eh2 = Math.floor(endMins / 60) % 24
      const em2 = Math.floor(endMins % 60)
      end = `${String(eh2).padStart(2, '0')}:${String(em2).padStart(2, '0')}`
      endMinutes = endMins % (24 * 60)
    } else {
      end = `${String(refH).padStart(2, '0')}:${String(refM).padStart(2, '0')}`
      endMinutes = refMinutes
      const startMins = refMinutes - durationHours * 60
      const sh2 = Math.floor((startMins + 24 * 60) / 60) % 24
      const sm2 = Math.floor(((startMins + 24 * 60) % 60))
      start = `${String(sh2).padStart(2, '0')}:${String(sm2).padStart(2, '0')}`
      startMinutes = (startMins + 24 * 60) % (24 * 60)
    }
  }

  const conflict = checkConflict(start, end, formTag.value, editingIndex.value)
  if (conflict) { notifyToast(conflict, 'error'); return }

  const duration = (endMinutes - startMinutes) / 60
  const originalRecord = isEditing.value ? records.value[editingIndex.value] : undefined
  const record: TimeRecord = {
    id: originalRecord?.id,
    todo_id: originalRecord?.todo_id,
    date: getTodayDate(), start, end, duration,
    content: formContent.value.trim(), tag: formTag.value
  }

  if (isEditing.value) {
    await appStore.updateRecord(editingIndex.value, record)
  } else {
    await appStore.addRecord(record)
  }
  showRecordForm.value = false
  resetRecordForm()
}

async function deleteRecord(index: number) {
  if (!confirm(t('legacyPlan.deleteRecordConfirm'))) return
  const record = records.value[index]
  await appStore.deleteRecord(index)
  if (record) {
    try { await unlinkTodoFromTimeRecord(record) } catch (error) { console.warn('Failed to clean deleted record link', error) }
  }
}

// ============ Management 相关状态 ============
type ManageView = 'overview' | 'plans' | 'editPlan' | 'rules' | 'editRule' | 'tempChange'
const manageView = ref<ManageView>('overview')

const editingPlanName = ref('')
const editingPlanType = ref<'切分制' | '分配制'>('切分制')
const editingPlanBgTag = ref('')
const editingPlanColor = ref([128, 128, 128])
const editingPlanItems = ref<PlanItem[]>([{ name: '', hours: 0 }, { name: '', hours: 0 }])

function openPlanList() { manageView.value = 'plans' }
function openCreatePlan() {
  editingPlanName.value = ''
  editingPlanType.value = '切分制'
  editingPlanBgTag.value = ''
  editingPlanColor.value = [128, 128, 128]
  editingPlanItems.value = [{ name: '', hours: 0 }, { name: '', hours: 0 }]
  manageView.value = 'editPlan'
}
function openEditPlan(name: string) {
  const plan = plans.value[name]
  if (!plan) return
  editingPlanName.value = name
  editingPlanType.value = plan.plan_type
  editingPlanBgTag.value = plan.bg_tag
  editingPlanColor.value = [...plan.color]
  editingPlanItems.value = plan.items.map(item => ({ ...item }))
  manageView.value = 'editPlan'
}
function addPlanItem() { editingPlanItems.value.push({ name: '', hours: 0 }) }
function removePlanItem(index: number) {
  const minCount = editingPlanType.value === '切分制' ? 2 : 1
  if (editingPlanItems.value.length <= minCount) return
  editingPlanItems.value.splice(index, 1)
}
async function savePlan() {
  const name = editingPlanName.value.trim()
  // 使用表单验证
  const valid = planValidation.validate({ planName: name })
  if (!valid) return
  const items = editingPlanItems.value.filter(item => item.name.trim())
  if (items.length === 0) { notifyToast(t('legacyPlan.validationCategoryRequired'), 'error'); return }
  for (const item of items) {
    if (item.hours < 0) { notifyToast(t('legacyPlan.validationHoursNegative', { name: item.name }), 'error'); return }
    if (item.hours > 24) { notifyToast(t('legacyPlan.validationHoursMax', { name: item.name }), 'error'); return }
  }
  if (editingPlanType.value === '切分制') {
    const total = items.reduce((sum, item) => sum + item.hours, 0)
    if (Math.abs(total - 24) > 0.01) {
      if (confirm(t('legacyPlan.balanceConfirm', { total }))) {
        editingPlanItems.value = autoBalance(items, 24)
      } else { return }
    }
  if (!editingPlanBgTag.value) { notifyToast(t('legacyPlan.backgroundRequired'), 'error'); return }
  }
  const newPlans = { ...plans.value }
  newPlans[name] = {
    plan_type: editingPlanType.value,
    items: editingPlanItems.value,
    bg_tag: editingPlanType.value === '切分制' ? editingPlanBgTag.value : '',
    color: editingPlanColor.value
  }
  await appStore.savePlans(newPlans)
  manageView.value = 'plans'
}
async function deletePlan(name: string) {
  if (!confirm(t('legacyPlan.deletePlanConfirm', { name }))) return
  const newPlans = { ...plans.value }
  delete newPlans[name]
  await appStore.savePlans(newPlans)
}

// 日程规则
const editingRuleIndex = ref(-1)
const editingRuleType = ref<'week' | 'month' | 'year' | 'month_week' | 'default'>('week')
const editingRuleValue = ref('')
const editingRulePlan = ref('')

function openRuleList() { manageView.value = 'rules' }
function openCreateRule() {
  editingRuleIndex.value = -1
  editingRuleType.value = 'week'
  editingRuleValue.value = ''
  editingRulePlan.value = Object.keys(plans.value)[0] || ''
  selectedWeekDays.value = new Set()
  manageView.value = 'editRule'
}
function openEditRule(index: number) {
  const rule = scheduleRules.value[index]
  if (!rule) return
  editingRuleIndex.value = index
  editingRuleType.value = rule.rule_type
  editingRuleValue.value = rule.value
  editingRulePlan.value = rule.plan_name
  // 如果是 week 类型，还原 selectedWeekDays
  if (rule.rule_type === 'week') {
    selectedWeekDays.value = new Set(rule.value.split(','))
  } else {
    selectedWeekDays.value = new Set()
  }
  manageView.value = 'editRule'
}
async function saveRule() {
  if (!editingRulePlan.value) { notifyToast(t('legacyPlan.relatedPlanRequired'), 'error'); return }
  if (editingRuleType.value === 'default') { notifyToast(t('legacyPlan.defaultRuleImmutable'), 'error'); return }

  // 对于 week 类型，从 selectedWeekDays 构建 value
  if (editingRuleType.value === 'week') {
  if (selectedWeekDays.value.size === 0) { notifyToast(t('legacyPlan.weekRequired'), 'error'); return }
    editingRuleValue.value = Array.from(selectedWeekDays.value).sort().join(',')
  }

  if (!editingRuleValue.value) { notifyToast(t('legacyPlan.ruleValueRequired'), 'error'); return }
  const newRule: ScheduleRule = {
    rule_type: editingRuleType.value,
    value: editingRuleValue.value,
    plan_name: editingRulePlan.value
  }
  const newRules = [...scheduleRules.value]
  if (editingRuleIndex.value === -1) {
    newRules.splice(newRules.length - 1, 0, newRule)
  } else {
    newRules[editingRuleIndex.value] = newRule
  }
  await appStore.saveScheduleRules(newRules)
  manageView.value = 'rules'
}
async function deleteRule(index: number) {
  if (!confirm(t('legacyPlan.deleteRuleConfirm'))) return
  const newRules = [...scheduleRules.value]
  newRules.splice(index, 1)
  await appStore.saveScheduleRules(newRules)
}
async function moveRuleUp(index: number) {
  if (index <= 0) return
  const newRules = [...scheduleRules.value]
  ;[newRules[index], newRules[index - 1]] = [newRules[index - 1], newRules[index]]
  await appStore.saveScheduleRules(newRules)
}

async function changeTodayPlan(planName: string) {
  if (planName === todayPlan.value.name) return
  await appStore.changeTodayPlan(planName)
  notifyToast(t('legacyPlan.switchedPlan', { name: planName }), 'success')
}

const weekDays = computed(() => [
  t('legacyPlan.weekday.mon'),
  t('legacyPlan.weekday.tue'),
  t('legacyPlan.weekday.wed'),
  t('legacyPlan.weekday.thu'),
  t('legacyPlan.weekday.fri'),
  t('legacyPlan.weekday.sat'),
  t('legacyPlan.weekday.sun'),
])
const selectedWeekDays = ref<Set<string>>(new Set())
function toggleWeekDay(day: string) {
  const num = (weekDays.value.indexOf(day) + 1).toString()
  if (selectedWeekDays.value.has(num)) selectedWeekDays.value.delete(num)
  else selectedWeekDays.value.add(num)
}
function isSelectedWeekDay(day: string): boolean {
  const num = (weekDays.value.indexOf(day) + 1).toString()
  return selectedWeekDays.value.has(num)
}

// ============ 今日汇总 ============
const todayTotalHours = computed(() => {
  return records.value.reduce((sum, r) => sum + r.duration, 0)
})

// ============ 辅助函数 ============
const TAG_COLORS = [
  '#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4'
]
const tagColorCache: Record<string, string> = {}
let tagColorIdx = 0

function getTagColorForName(name: string): string {
  if (tagColorCache[name]) return tagColorCache[name]
  const color = TAG_COLORS[tagColorIdx % TAG_COLORS.length]
  tagColorCache[name] = color
  tagColorIdx++
  return color
}

function getTagColor(tag: string): string {
  return getTagColorForName(tag)
}

function getPlanItemColor(itemName: string): string {
  return getTagColorForName(itemName)
}

// 记录表单验证规则
const recordValidation = useFormValidation({
  content: { required: t('legacyPlan.contentRequired'), min: 1 },
  tag: { required: t('legacyPlan.categoryRequired') },
})

const recordFormErrors = recordValidation.errors

// 计划表单验证规则
const planValidation = useFormValidation({
  planName: { required: t('legacyPlan.planNameRequired'), min: 1 },
})

const planFormErrors = planValidation.errors

// 实时验证 - 记录表单
function validateRecordField(field: 'content' | 'tag', value: string) {
  recordValidation.validateOne(field, value)
}

// 实时验证 - 计划表单
function validatePlanField(field: 'planName', value: string) {
  planValidation.validateOne(field, value)
}

onMounted(() => {
  formTag.value = availableTags.value[0] || ''
})
</script>

<template>
  <div class="plan-view">
    <!-- 顶部导航栏 -->
    <header class="pv-header">
      <button class="pv-back" @click="AudioManager.playSound('click'); router.push('/plans')">
        <ArrowLeft :size="18" />
      </button>
      <div class="pv-header-title">
        <Clock :size="18" />
        <span>{{ t('legacyPlan.title') }}</span>
      </div>
      <div class="pv-header-actions">
        <button class="pv-add-btn" @click="AudioManager.playSound('click'); openAddForm()">
          <Plus :size="16" />
          <span>{{ t('legacyPlan.add') }}</span>
        </button>
      </div>
    </header>

    <!-- 内容区域 -->
    <main class="pv-content">
      <Transition name="tab-fade" mode="out-in">
        <!-- ============ 统一计划工作台 ============ -->
        <div v-if="manageView === 'overview'" key="overview" class="pv-panel">
          <!-- 今日概览卡片 -->
          <div class="pv-summary-card">
            <div class="pv-summary-left">
              <span class="pv-summary-label">{{ t('legacyPlan.todayRecorded') }}</span>
              <span class="pv-summary-value">{{ hoursToHm(todayTotalHours) }}</span>
            </div>
            <div class="pv-summary-right">
              <span class="pv-summary-plan">{{ todayPlan.name }}</span>
              <span class="pv-summary-count">{{ records.length }} {{ t('legacyPlan.recordsCount') }}</span>
            </div>
          </div>

          <!-- 记录列表 -->
          <div class="pv-records" v-if="records.length > 0">
            <TransitionGroup name="list">
              <div
                v-for="(record, index) in records"
                :key="`${record.start}-${record.tag}`"
                class="pv-record-card"
              >
                <div class="pv-record-color" :style="{ background: getTagColor(record.tag) }"></div>
                <div class="pv-record-body">
                  <div class="pv-record-top">
                    <span class="pv-record-tag">{{ record.tag }}</span>
                    <span class="pv-record-time">{{ record.start }} — {{ record.end }}</span>
                  </div>
                  <div class="pv-record-content">{{ record.content }}</div>
                  <div class="pv-record-meta">{{ hoursToHm(record.duration) }}</div>
                </div>
                <div class="pv-record-actions">
                  <button class="pv-icon-btn" @click="AudioManager.playSound('click'); openEditForm(index)" :title="t('legacyPlan.edit')">
                    <Pencil :size="14" />
                  </button>
                  <button class="pv-icon-btn danger" @click="AudioManager.playSound('click'); deleteRecord(index)" :title="t('legacyPlan.delete')">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </TransitionGroup>
          </div>

          <!-- 空状态 -->
          <EmptyState
            v-else
            :icon="ClipboardList"
              :title="t('legacyPlan.emptyRecords')"
              :description="t('legacyPlan.emptyRecordsHint')"
            @action="AudioManager.playSound('click'); openAddForm()"
          />

          <!-- 计划管理与记录共用同一工作台，不再拆成独立顶层页面 -->
          <section class="pv-management-summary">
            <div class="pv-plan-hero">
              <div class="pv-plan-hero-header">
                <span class="pv-plan-hero-label">{{ t('legacyPlan.todayPlan') }}</span>
                <div class="pv-plan-hero-tools">
                  <span class="pv-plan-hero-badge">{{ todayPlan.type }}</span>
                  <button class="pv-inline-btn" @click="AudioManager.playSound('click'); openEditPlan(todayPlan.name)" :title="t('legacyPlan.edit')">
                    <Pencil :size="14" />
                    <span>{{ t('legacyPlan.edit') }}</span>
                  </button>
                </div>
              </div>
              <div class="pv-plan-selector-row">
                <label class="pv-plan-selector-label" for="today-plan-select">{{ t('legacyPlan.currentTodayPlan') }}</label>
                <select
                  id="today-plan-select"
                  class="pv-plan-selector"
                  :value="todayPlan.name"
                  @change="changeTodayPlan(($event.target as HTMLSelectElement).value)"
                >
                  <option v-for="(plan, name) in plans" :key="name" :value="name">{{ name }} · {{ plan.plan_type }}</option>
                </select>
                <button class="pv-inline-btn pv-inline-btn-primary" @click="AudioManager.playSound('click'); openCreatePlan()">
                  <Plus :size="14" />
                  <span>{{ t('legacyPlan.create') }}</span>
                </button>
              </div>
              <h2 class="pv-plan-hero-name">{{ todayPlan.name }}</h2>
              <div class="pv-plan-hero-items" v-if="plans[todayPlan.name]">
                <div v-for="item in plans[todayPlan.name].items" :key="item.name" class="pv-plan-hero-item">
                  <span class="pv-plan-item-dot" :style="{ background: getPlanItemColor(item.name) }"></span>
                  <span>{{ item.name }}</span>
                  <span class="pv-plan-item-hours">{{ item.hours }}h</span>
                </div>
              </div>
            </div>
            <div class="pv-action-cards">
              <button class="pv-action-card" @click="AudioManager.playSound('click'); openPlanList()">
                <div class="pv-action-icon" style="--icon-bg: rgba(99,102,241,0.12); --icon-color: #6366f1;"><FolderKanban :size="22" /></div>
                <div class="pv-action-text"><span class="pv-action-title">{{ t('legacyPlan.planManagement') }}</span><span class="pv-action-desc">{{ t('legacyPlan.planManagementDescription') }}</span></div>
                <ChevronRight :size="16" class="pv-action-arrow" />
              </button>
              <button class="pv-action-card" @click="AudioManager.playSound('click'); openRuleList()">
                <div class="pv-action-icon" style="--icon-bg: rgba(34,197,94,0.12); --icon-color: #22c55e;"><Calendar :size="22" /></div>
                <div class="pv-action-text"><span class="pv-action-title">{{ t('legacyPlan.scheduleRules') }}</span><span class="pv-action-desc">{{ t('legacyPlan.scheduleRulesDescription') }}</span></div>
                <ChevronRight :size="16" class="pv-action-arrow" />
              </button>
              <button class="pv-action-card" @click="AudioManager.playSound('click'); manageView = 'tempChange'">
                <div class="pv-action-icon" style="--icon-bg: rgba(245,158,11,0.12); --icon-color: #f59e0b;"><RefreshCw :size="22" /></div>
                <div class="pv-action-text"><span class="pv-action-title">{{ t('legacyPlan.temporaryChange') }}</span><span class="pv-action-desc">{{ t('legacyPlan.temporaryChangeDescription') }}</span></div>
                <ChevronRight :size="16" class="pv-action-arrow" />
              </button>
            </div>
          </section>
        </div>

        <!-- ============ 管理二级视图 ============ -->
        <div v-else key="manage" class="pv-panel">
          <!-- 管理子视图 -->

          <!-- 日计划列表 -->
          <template v-if="manageView === 'plans'">
            <div class="pv-sub-header">
              <button class="pv-back-link" @click="AudioManager.playSound('click'); manageView = 'overview'">
                <ArrowLeft :size="14" />
                <span>{{ t('legacyPlan.back') }}</span>
              </button>
              <h2>{{ t('legacyPlan.plans') }}</h2>
              <button class="pv-primary-btn" @click="AudioManager.playSound('click'); openCreatePlan()">
                <Plus :size="14" />
                <span>{{ t('legacyPlan.create') }}</span>
              </button>
            </div>
            <div class="pv-plan-list">
              <div v-for="(plan, name) in plans" :key="name" class="pv-plan-card">
                <div class="pv-plan-color" :style="{ background: rgbToHex(plan.color[0], plan.color[1], plan.color[2]) }"></div>
                <div class="pv-plan-info">
                  <div class="pv-plan-title">{{ name }}</div>
                  <div class="pv-plan-meta">
                    {{ plan.plan_type }}
                    <template v-if="plan.plan_type === '分配制'">
                       · {{ plan.items.reduce((s, i) => s + i.hours, 0).toFixed(1) }}h
                    </template>
                    <template v-else-if="plan.bg_tag">
                  · {{ t('legacyPlan.backgroundPrefix') }}{{ plan.bg_tag }}
                    </template>
                  </div>
                </div>
                <div class="pv-plan-actions">
                  <button class="pv-icon-btn" @click="AudioManager.playSound('click'); openEditPlan(name as string)" :title="t('legacyPlan.edit')">
                    <Pencil :size="14" />
                  </button>
                  <button class="pv-icon-btn danger" @click="AudioManager.playSound('click'); deletePlan(name as string)" :title="t('legacyPlan.delete')">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </template>

          <!-- 编辑日计划 -->
          <template v-else-if="manageView === 'editPlan'">
            <div class="pv-sub-header">
              <button class="pv-back-link" @click="AudioManager.playSound('click'); manageView = 'plans'">
                <ArrowLeft :size="14" />
                <span>{{ t('legacyPlan.back') }}</span>
              </button>
              <h2>{{ editingPlanName ? t('legacyPlan.editPlan') : t('legacyPlan.createPlan') }}</h2>
              <div></div>
            </div>

            <div class="pv-form-group">
              <label>{{ t('legacyPlan.planName') }}</label>
              <input
                type="text"
                v-model="editingPlanName"
                class="pv-text-input"
                :class="{ 'has-error': planFormErrors.planName }"
                :placeholder="t('legacyPlan.planNamePlaceholder')"
                @blur="validatePlanField('planName', editingPlanName)"
              />
              <p v-if="planFormErrors.planName" class="pv-field-error">{{ planFormErrors.planName }}</p>
            </div>

            <div class="pv-form-group">
              <label>{{ t('legacyPlan.planType') }}</label>
              <div class="pv-type-toggle">
                <button :class="{ active: editingPlanType === '切分制' }" @click="editingPlanType = '切分制'">{{ t('legacyPlan.split') }}</button>
                <button :class="{ active: editingPlanType === '分配制' }" @click="editingPlanType = '分配制'">{{ t('legacyPlan.allocate') }}</button>
              </div>
            </div>

            <div class="pv-form-group">
              <label>{{ t('legacyPlan.categories') }}</label>
              <div class="pv-items">
                <div v-for="(item, index) in editingPlanItems" :key="index" class="pv-item-row">
                  <input type="text" v-model="item.name" :placeholder="t('legacyPlan.categoryName')" class="pv-text-input flex-1" />
                  <input type="number" v-model="item.hours" :placeholder="t('legacyPlan.hours')" class="pv-num-input" step="0.5" />
                  <span class="pv-unit">h</span>
                  <button
                    v-if="editingPlanType === '切分制'"
                    class="pv-bg-toggle"
                    :class="{ active: editingPlanBgTag === item.name }"
                    @click="editingPlanBgTag = item.name"
                  >{{ t('legacyPlan.background') }}</button>
                  <button class="pv-icon-btn sm" @click="removePlanItem(index)">
                    <X :size="12" />
                  </button>
                </div>
              </div>
              <button class="pv-secondary-btn" @click="addPlanItem()">
                <Plus :size="14" />
                <span>{{ t('legacyPlan.addCategory') }}</span>
              </button>
            </div>

            <div class="pv-form-footer">
              <button class="pv-secondary-btn" @click="AudioManager.playSound('click'); manageView = 'plans'">{{ t('legacyPlan.cancel') }}</button>
              <button class="pv-primary-btn" @click="AudioManager.playSound('click'); savePlan()">
                <Check :size="14" />
                <span>{{ t('legacyPlan.save') }}</span>
              </button>
            </div>
          </template>

          <!-- 日程规则列表 -->
          <template v-else-if="manageView === 'rules'">
            <div class="pv-sub-header">
              <button class="pv-back-link" @click="AudioManager.playSound('click'); manageView = 'overview'">
                <ArrowLeft :size="14" />
                <span>{{ t('legacyPlan.back') }}</span>
              </button>
              <h2>{{ t('legacyPlan.rules') }}</h2>
              <button class="pv-primary-btn" @click="AudioManager.playSound('click'); openCreateRule()">
                <Plus :size="14" />
                <span>{{ t('legacyPlan.addRule') }}</span>
              </button>
            </div>
            <div class="pv-rule-list">
              <div v-for="(rule, index) in scheduleRules" :key="index" class="pv-rule-card">
                <div class="pv-rule-info">
                  <template v-if="rule.rule_type === 'week'">
                    <span class="pv-rule-type-badge">{{ t('legacyPlan.week') }}</span>
                    {{ t('legacyPlan.weekLabel') }} {{ rule.value.split(',').map(v => weekDays[parseInt(v) - 1]).join('、') }} → <strong>{{ rule.plan_name }}</strong>
                  </template>
                  <template v-else-if="rule.rule_type === 'month'">
                    <span class="pv-rule-type-badge">{{ t('legacyPlan.month') }}</span>
                    {{ rule.value.split(',').map(v => v + t('legacyPlan.monthLabel')).join('、') }} → <strong>{{ rule.plan_name }}</strong>
                  </template>
                  <template v-else-if="rule.rule_type === 'year'">
                    <span class="pv-rule-type-badge">{{ t('legacyPlan.year') }}</span>
                    {{ t('legacyPlan.yearLabel') }} {{ rule.value }} → <strong>{{ rule.plan_name }}</strong>
                  </template>
                  <template v-else-if="rule.rule_type === 'month_week'">
                    <span class="pv-rule-type-badge">{{ t('legacyPlan.monthWeek') }}</span>
                    {{ t('legacyPlan.monthWeekLabel') }}{{ rule.value.split('-')[0] }}{{ t('legacyPlan.monthWeekSuffix') }}{{ weekDays[parseInt(rule.value.split('-')[1]) - 1] }} → <strong>{{ rule.plan_name }}</strong>
                  </template>
                  <template v-else>
                    <span class="pv-rule-type-badge default">{{ t('legacyPlan.defaultRule') }}</span>
                    {{ t('legacyPlan.defaultRule') }} → <strong>{{ rule.plan_name }}</strong>
                  </template>
                </div>
                <div class="pv-rule-actions" v-if="rule.rule_type !== 'default'">
                  <button class="pv-icon-btn" @click="AudioManager.playSound('click'); openEditRule(index)" :title="t('legacyPlan.edit')">
                    <Pencil :size="14" />
                  </button>
                  <button class="pv-icon-btn" @click="AudioManager.playSound('click'); moveRuleUp(index)" :title="t('legacyPlan.moveUp')">↑</button>
                  <button class="pv-icon-btn danger" @click="AudioManager.playSound('click'); deleteRule(index)" :title="t('legacyPlan.delete')">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </template>

          <!-- 编辑规则 -->
          <template v-else-if="manageView === 'editRule'">
            <div class="pv-sub-header">
              <button class="pv-back-link" @click="AudioManager.playSound('click'); manageView = 'rules'">
                <ArrowLeft :size="14" />
                <span>{{ t('legacyPlan.back') }}</span>
              </button>
              <h2>{{ editingRuleIndex === -1 ? t('legacyPlan.addRule') : t('legacyPlan.edit') }}</h2>
              <div></div>
            </div>

            <div class="pv-form-group">
              <label>{{ t('legacyPlan.rules') }}</label>
              <div class="pv-type-toggle wrap">
                <button :class="{ active: editingRuleType === 'week' }" @click="editingRuleType = 'week'">{{ t('legacyPlan.week') }}</button>
                <button :class="{ active: editingRuleType === 'month' }" @click="editingRuleType = 'month'">{{ t('legacyPlan.month') }}</button>
                <button :class="{ active: editingRuleType === 'year' }" @click="editingRuleType = 'year'">{{ t('legacyPlan.year') }}</button>
                <button :class="{ active: editingRuleType === 'month_week' }" @click="editingRuleType = 'month_week'">{{ t('legacyPlan.monthWeek') }}</button>
              </div>
            </div>

            <div class="pv-form-group" v-if="editingRuleType === 'week'">
              <label>{{ t('legacyPlan.selectWeek') }}</label>
              <div class="pv-week-picker">
                <button
                  v-for="day in weekDays"
                  :key="day"
                  class="pv-week-btn"
                  :class="{ active: isSelectedWeekDay(day) }"
                  @click="toggleWeekDay(day)"
                >{{ day }}</button>
              </div>
            </div>

            <div class="pv-form-group" v-if="editingRuleType === 'month'">
              <label>{{ t('legacyPlan.monthHint') }}</label>
              <input type="text" v-model="editingRuleValue" class="pv-text-input" :placeholder="t('legacyPlan.monthPlaceholder')" />
            </div>

            <div class="pv-form-group" v-if="editingRuleType === 'year'">
              <label>{{ t('legacyPlan.dateHint') }}</label>
              <input type="text" v-model="editingRuleValue" class="pv-text-input" :placeholder="t('legacyPlan.datePlaceholder')" />
            </div>

            <div class="pv-form-group" v-if="editingRuleType === 'month_week'">
              <label>{{ t('legacyPlan.monthWeekHint') }}</label>
              <input type="text" v-model="editingRuleValue" class="pv-text-input" :placeholder="t('legacyPlan.monthWeekPlaceholder')" />
            </div>

            <div class="pv-form-group">
              <label>{{ t('legacyPlan.relatedPlan') }}</label>
              <select v-model="editingRulePlan" class="pv-select">
                <option v-for="name in Object.keys(plans)" :key="name" :value="name">{{ name }}</option>
              </select>
            </div>

            <div class="pv-form-footer">
              <button class="pv-secondary-btn" @click="AudioManager.playSound('click'); manageView = 'rules'">{{ t('legacyPlan.cancel') }}</button>
              <button class="pv-primary-btn" @click="AudioManager.playSound('click'); saveRule()">
                <Check :size="14" />
                <span>{{ t('legacyPlan.save') }}</span>
              </button>
            </div>
          </template>

          <!-- 临时计划变更 -->
          <template v-else-if="manageView === 'tempChange'">
            <div class="pv-sub-header">
              <button class="pv-back-link" @click="AudioManager.playSound('click'); manageView = 'overview'">
                <ArrowLeft :size="14" />
                <span>{{ t('legacyPlan.back') }}</span>
              </button>
              <h2>{{ t('legacyPlan.tempPlan') }}</h2>
              <div></div>
            </div>

            <div class="pv-current-info">
                <span>{{ t('legacyPlan.currentTodayPlan') }}</span>
              <strong>{{ todayPlan.name }}</strong>
            </div>

            <div class="pv-plan-pick-list">
              <button
                v-for="(plan, name) in plans"
                :key="name"
                class="pv-plan-pick"
                :class="{ current: name === todayPlan.name }"
                :disabled="name === todayPlan.name"
                @click="AudioManager.playSound('click'); changeTodayPlan(name as string)"
              >
                <span class="pv-plan-pick-name">{{ name }}</span>
                <span class="pv-plan-pick-type">{{ plan.plan_type }}</span>
                <Check v-if="name === todayPlan.name" :size="16" />
              </button>
            </div>
          </template>
        </div>
      </Transition>
    </main>

    <!-- 记录表单弹窗 -->
    <Transition name="modal">
      <div v-if="showRecordForm" class="pv-modal-overlay" @click.self="showRecordForm = false">
        <div class="pv-modal">
          <div class="pv-modal-header">
            <h3>{{ isEditing ? t('legacyPlan.recordEdit') : t('legacyPlan.recordAdd') }}</h3>
            <button class="pv-modal-close" @click="showRecordForm = false">
              <X :size="18" />
            </button>
          </div>
          <div class="pv-modal-body">
            <!-- 输入模式切换 -->
            <div class="pv-mode-toggle">
              <button :class="{ active: formMode === 'time' }" @click="formMode = 'time'">{{ t('legacyPlan.startEnd') }}</button>
              <button :class="{ active: formMode === 'duration' }" @click="formMode = 'duration'">{{ t('legacyPlan.durationPoint') }}</button>
            </div>

            <div class="pv-form-group" v-if="formMode === 'time'">
              <label>{{ t('legacyPlan.start') }}</label>
              <div class="pv-time-row">
                <input type="number" v-model="formStart.h" min="0" max="23" class="pv-num-input" />
                <span class="pv-time-sep">:</span>
                <input type="number" v-model="formStart.m" min="0" max="59" class="pv-num-input" />
              </div>
            </div>
            <div class="pv-form-group" v-if="formMode === 'time'">
              <label>{{ t('legacyPlan.end') }}</label>
              <div class="pv-time-row">
                <input type="number" v-model="formEnd.h" min="0" max="23" class="pv-num-input" />
                <span class="pv-time-sep">:</span>
                <input type="number" v-model="formEnd.m" min="0" max="59" class="pv-num-input" />
              </div>
            </div>

            <div class="pv-form-group" v-if="formMode === 'duration'">
              <label>{{ t('legacyPlan.duration') }}</label>
              <div class="pv-time-row">
                <input type="number" v-model="formDuration.h" min="0" class="pv-num-input sm" />
                <span class="pv-time-unit">{{ t('legacyPlan.hourUnit') }}</span>
                <input type="number" v-model="formDuration.m" min="0" max="59" class="pv-num-input sm" />
                <span class="pv-time-unit">{{ t('legacyPlan.minuteUnit') }}</span>
              </div>
            </div>
            <div class="pv-form-group" v-if="formMode === 'duration'">
              <label>{{ t('legacyPlan.referenceTime') }}</label>
              <div class="pv-time-row">
                <input type="number" v-model="formDurationTime.h" min="0" max="23" class="pv-num-input" />
                <span class="pv-time-sep">:</span>
                <input type="number" v-model="formDurationTime.m" min="0" max="59" class="pv-num-input" />
              </div>
            </div>
            <div class="pv-form-group" v-if="formMode === 'duration'">
              <label>{{ t('legacyPlan.referenceType') }}</label>
              <div class="pv-radio-group">
                <label><input type="radio" v-model="formDurationRef" value="start" /><span>{{ t('legacyPlan.referenceStart') }}</span></label>
                <label><input type="radio" v-model="formDurationRef" value="end" /><span>{{ t('legacyPlan.referenceEnd') }}</span></label>
              </div>
            </div>

            <div class="pv-form-group">
              <label>{{ t('legacyPlan.content') }}</label>
              <input
                type="text"
                v-model="formContent"
                :placeholder="t('legacyPlan.contentPlaceholder')"
                class="pv-text-input"
                :class="{ 'has-error': recordFormErrors.content }"
                @blur="validateRecordField('content', formContent)"
              />
              <p v-if="recordFormErrors.content" class="pv-field-error">{{ recordFormErrors.content }}</p>
            </div>

            <div class="pv-form-group">
              <label>{{ t('legacyPlan.category') }}</label>
              <select
                v-model="formTag"
                class="pv-select"
                :class="{ 'has-error': recordFormErrors.tag }"
                @blur="validateRecordField('tag', formTag)"
              >
                <option v-for="tag in availableTags" :key="tag" :value="tag">{{ tag }}</option>
              </select>
              <p v-if="recordFormErrors.tag" class="pv-field-error">{{ recordFormErrors.tag }}</p>
            </div>
          </div>
          <div class="pv-modal-footer">
            <button class="pv-secondary-btn" @click="showRecordForm = false">{{ t('legacyPlan.cancel') }}</button>
            <button class="pv-primary-btn" @click="AudioManager.playSound('click'); saveRecord()">
              <Check :size="14" />
              <span>{{ t('legacyPlan.save') }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.plan-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

/* ============ Header ============ */
.pv-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  position: sticky;
  top: 0;
  z-index: 10;
}

.pv-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}
.pv-back:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.pv-tabs {
  flex: 1;
  display: flex;
  position: relative;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  padding: 3px;
  gap: 2px;
}

.pv-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: calc(var(--radius-md) - 2px);
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
  font-weight: 500;
  z-index: 1;
  transition: color var(--transition-fast);
}
.pv-tab:hover {
  color: var(--color-text-secondary);
}
.pv-tab.active {
  color: var(--color-text-primary);
  font-weight: 600;
}

.pv-tab-indicator {
  position: absolute;
  top: 3px;
  left: 3px;
  width: calc(50% - 4px);
  height: calc(100% - 6px);
  background: var(--color-bg);
  border-radius: calc(var(--radius-md) - 2px);
  box-shadow: var(--shadow-sm);
  transition: transform var(--transition-normal);
}
.pv-tab-indicator.right {
  transform: translateX(calc(100% + 3px));
}

.pv-header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.pv-add-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 0.8125rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.pv-add-btn:hover {
  background: var(--color-primary-hover);
  color: white;
}

.pv-add-btn:active {
  transform: scale(0.95);
}

/* ============ Content ============ */
.pv-content {
  flex: 1;
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
  padding: var(--spacing-lg);
}

.pv-panel {
  animation: panelIn 0.2s ease-out;
}

@keyframes panelIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Tab transition */
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.tab-fade-enter-from { opacity: 0; transform: translateX(12px); }
.tab-fade-leave-to { opacity: 0; transform: translateX(-12px); }

/* ============ Summary Card ============ */
.pv-summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  background: linear-gradient(135deg, var(--color-bg-secondary) 0%, var(--color-bg-tertiary) 100%);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-lg);
}

.pv-summary-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pv-summary-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.pv-summary-value {
  font-size: 1.75rem;
  font-weight: 800;
  font-family: var(--font-mono);
  color: var(--color-text-primary);
  line-height: 1;
}

.pv-summary-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}
.pv-summary-plan {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-primary);
  padding: 2px 10px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: var(--radius-full);
}
.pv-summary-count {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* ============ Records List ============ */
.pv-records {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.pv-record-card {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}
.pv-record-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-sm);
}

.pv-record-color {
  width: 4px;
  border-radius: 2px;
  flex-shrink: 0;
  align-self: stretch;
}

.pv-record-body {
  flex: 1;
  min-width: 0;
}
.pv-record-top {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: 4px;
}
.pv-record-tag {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-primary);
  padding: 1px 8px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: var(--radius-full);
}
.pv-record-time {
  font-size: 0.8125rem;
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
}
.pv-record-content {
  font-size: 0.875rem;
  color: var(--color-text-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pv-record-meta {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  font-family: var(--font-mono);
}

.pv-record-actions {
  display: flex;
  gap: var(--spacing-xs);
  align-items: flex-start;
  padding-top: 2px;
}

/* List transition */
.list-enter-active,
.list-leave-active {
  transition: all 0.25s ease;
}
.list-enter-from { opacity: 0; transform: translateX(-16px); }
.list-leave-to { opacity: 0; transform: translateX(16px); }
.list-move { transition: transform 0.25s ease; }

/* ============ Empty State ============ */
/* 使用通用 EmptyState 组件 */

/* ============ Management Views ============ */
.pv-plan-hero {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}
.pv-plan-hero-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}
.pv-plan-hero-tools {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.pv-inline-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  transition: all var(--transition-fast);
}
.pv-inline-btn:hover,
.pv-inline-btn:focus-visible {
  border-color: var(--color-primary);
  color: var(--color-primary);
  outline: none;
}
.pv-inline-btn-primary {
  border-color: var(--color-primary-muted);
  color: var(--color-primary);
}
.pv-plan-selector-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}
.pv-plan-selector-label {
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  white-space: nowrap;
}
.pv-plan-selector {
  min-width: 0;
  flex: 1;
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-size: 0.8125rem;
}
.pv-plan-selector:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
.pv-plan-hero-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.pv-plan-hero-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 2px 8px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
  border-radius: var(--radius-full);
}
.pv-plan-hero-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}
.pv-plan-hero-items {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}
.pv-plan-hero-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}
.pv-plan-item-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.pv-plan-item-hours {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* ============ Action Cards ============ */
.pv-action-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.pv-action-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  text-align: left;
  transition: all var(--transition-fast);
}
.pv-action-card:hover {
  border-color: var(--color-border-hover);
  background: transparent;
  transform: translateY(-1px);
  box-shadow: 0 0 0 1px var(--color-border-hover), var(--shadow-sm);
}

.pv-action-card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 3px;
  background: transparent;
}

.pv-header-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-text-primary);
  font-weight: 600;
}

.pv-management-summary {
  display: grid;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.pv-action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--icon-bg);
  color: var(--icon-color);
  flex-shrink: 0;
}
.pv-action-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.pv-action-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary);
}
.pv-action-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}
.pv-action-arrow {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

/* ============ Sub-headers ============ */
.pv-sub-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}
.pv-sub-header h2 {
  flex: 1;
  font-size: 1.125rem;
  font-weight: 600;
}

.pv-back-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}
.pv-back-link:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-secondary);
}

/* ============ Plan List ============ */
.pv-plan-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.pv-plan-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}
.pv-plan-card:hover {
  border-color: var(--color-border-hover);
}
.pv-plan-color {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
}
.pv-plan-info { flex: 1; }
.pv-plan-title { font-weight: 500; font-size: 0.875rem; }
.pv-plan-meta {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}
.pv-plan-actions {
  display: flex;
  gap: var(--spacing-xs);
}

/* ============ Rule List ============ */
.pv-rule-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.pv-rule-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.pv-rule-info { flex: 1; font-size: 0.8125rem; color: var(--color-text-secondary); }
.pv-rule-type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 20px;
  padding: 0 6px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 0.625rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-right: 6px;
}
.pv-rule-type-badge.default {
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
}
.pv-rule-actions {
  display: flex;
  gap: var(--spacing-xs);
}

/* ============ Plan Pick (临时变更) ============ */
.pv-current-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-lg);
}
.pv-current-info span {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}
.pv-current-info strong {
  font-size: 1rem;
  color: var(--color-primary);
}

.pv-plan-pick-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.pv-plan-pick {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  text-align: left;
  transition: all var(--transition-fast);
}
.pv-plan-pick:hover:not(:disabled) {
  border-color: var(--color-border-hover);
  background: var(--color-bg-tertiary);
}
.pv-plan-pick.current {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}
.pv-plan-pick-name {
  flex: 1;
  font-weight: 500;
}
.pv-plan-pick-type {
  font-size: 0.75rem;
  opacity: 0.6;
}

/* ============ Forms ============ */
.pv-form-group {
  margin-bottom: var(--spacing-lg);
}
.pv-form-group label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.pv-text-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  transition: border-color var(--transition-fast);
}
.pv-text-input:focus {
  outline: none;
  border-color: var(--color-primary);
}
.pv-text-input.has-error {
  border-color: var(--color-error);
}
.pv-text-input.flex-1 { flex: 1; }

/* 字段错误提示 */
.pv-field-error {
  font-size: 0.75rem;
  color: var(--color-error);
  margin: var(--spacing-xs) 0 0 0;
  animation: fieldErrorIn 0.2s ease-out;
}

@keyframes fieldErrorIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.pv-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 0.875rem;
}
.pv-select:focus {
  outline: none;
  border-color: var(--color-primary);
}
.pv-select.has-error {
  border-color: var(--color-error);
}

.pv-num-input {
  width: 64px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  text-align: center;
  font-family: var(--font-mono);
  font-size: 0.875rem;
}
.pv-num-input.sm { width: 48px; }
.pv-num-input:focus { outline: none; border-color: var(--color-primary); }

.pv-time-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.pv-time-sep {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--color-text-tertiary);
}
.pv-time-unit {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.pv-radio-group {
  display: flex;
  gap: var(--spacing-lg);
}
.pv-radio-group label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  margin-bottom: 0;
  font-size: 0.8125rem;
}

.pv-type-toggle {
  display: flex;
  gap: 2px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  padding: 3px;
  border: 1px solid var(--color-border);
}
.pv-type-toggle button {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: calc(var(--radius-md) - 2px);
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.pv-type-toggle button.active {
  background: var(--color-bg);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}
.pv-type-toggle.wrap {
  flex-wrap: wrap;
}
.pv-type-toggle.wrap button {
  flex: 0 0 auto;
}

.pv-week-picker {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}
.pv-week-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  transition: all var(--transition-fast);
}
.pv-week-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.pv-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}
.pv-item-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.pv-unit {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}
.pv-bg-toggle {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-tertiary);
  font-size: 0.6875rem;
  transition: all var(--transition-fast);
}
.pv-bg-toggle.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.pv-form-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xl);
}

/* ============ Buttons ============ */
.pv-primary-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 0.8125rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.pv-primary-btn:hover {
  background: var(--color-primary-hover);
  color: white;
}

.pv-primary-btn:active {
  transform: scale(0.96);
}

.pv-secondary-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.8125rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.pv-secondary-btn:hover {
  background: var(--color-bg-tertiary);
}

.pv-secondary-btn:active {
  transform: scale(0.96);
}

.pv-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}
.pv-icon-btn.sm {
  width: 24px;
  height: 24px;
}
.pv-icon-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}
.pv-icon-btn.danger:hover {
  background: var(--color-error);
  border-color: var(--color-error);
  color: white;
}

/* ============ Modal ============ */
.pv-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.pv-modal {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.pv-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}
.pv-modal-header h3 {
  font-size: 1rem;
  font-weight: 600;
}
.pv-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-tertiary);
  transition: all var(--transition-fast);
}
.pv-modal-close:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}
.pv-modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
}
.pv-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.pv-mode-toggle {
  display: flex;
  gap: 2px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  padding: 3px;
  margin-bottom: var(--spacing-lg);
  border: 1px solid var(--color-border);
}
.pv-mode-toggle button {
  flex: 1;
  padding: var(--spacing-sm);
  border: none;
  border-radius: calc(var(--radius-md) - 2px);
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.pv-mode-toggle button.active {
  background: var(--color-bg);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .pv-modal,
.modal-leave-active .pv-modal {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .pv-modal,
.modal-leave-to .pv-modal {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}
</style>
