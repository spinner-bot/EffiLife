<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { hoursToHm, parseStoredDate } from '@/services/dataService'
import { ClipboardList, Clock3, Flame, Inbox, Bell, CheckCircle, Check, ChevronRight, X, Inbox as InboxIcon, ListTodo, Plus } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import { EventSystem } from '@/audio'
import { checkinState } from '@/data'
import EmptyState from '@/components/EmptyState.vue'
import { TodoCategoryService, TodoService, type UnifiedTodo } from '@/services/todoService'
import { getPriorityScore } from '@/services/priority'
import { listPlanSummaries, planDataSource, type PlanGatewayState, type PlanSummary } from '@/services/planGateway'
import { isMobilePlanRuntime } from '@/services/runtimeCapabilities'
import { getNotificationIcon } from '@/services/notificationIcons'
import { useI18n } from '@/i18n'
import { notifyToast } from '@/services/toastService'
import { onWorkspaceChanged } from '@/services/workspaceEvents'

const router = useRouter()
const appStore = useAppStore()
const { t, locale } = useI18n()

const currentTime = ref('')
const currentDate = ref('')
let timer: number | null = null
let refreshTimer: number | null = null
let workspaceRefreshTimer: number | null = null
let summaryRefreshRunning = false
let summaryRefreshQueued = false
let todoSummaryRequestId = 0
let eventPlanSummaryRequestId = 0
const activeTodoCount = ref(0)
const todayTodos = ref<UnifiedTodo[]>([])
const todoSummaryUnavailable = ref(false)
const timeSummaryUnavailable = ref(false)
const workspaceSummaryReady = ref(false)
const quickTodoTitle = ref('')
const quickTodoSaving = ref(false)
const completingTodoId = ref<string | null>(null)
const eventPlans = ref<PlanSummary[]>([])
const eventPlanState = ref<PlanGatewayState>('idle')
const mobilePlanRuntime = isMobilePlanRuntime()

function openDailyPlan() {
  router.push('/time')
}

function openEventPlan(plan: PlanSummary) {
  router.push({ path: '/plans', query: { plan: plan.id } })
}

async function refreshTodoSummary() {
  const requestId = ++todoSummaryRequestId
  try {
    const [todos, categories] = await Promise.all([
      TodoService.list(),
      TodoCategoryService.list().catch(() => []),
    ])
    const categoryById = new Map(categories.map((category) => [category.id, category]))
    const active = todos.filter((todo) => !['completed', 'archived', 'cancelled'].includes(todo.status))
    if (requestId !== todoSummaryRequestId) return
    const today = new Date()
    const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()
    const urgency = (todo: UnifiedTodo): { rank: number; timestamp: number } => {
      if (!todo.deadline) return { rank: 3, timestamp: Number.POSITIVE_INFINITY }
      const deadline = parseStoredDate(todo.deadline)
      if (Number.isNaN(deadline.getTime())) return { rank: 3, timestamp: Number.POSITIVE_INFINITY }
      const deadlineStart = new Date(deadline.getFullYear(), deadline.getMonth(), deadline.getDate()).getTime()
      if (deadlineStart < todayStart) return { rank: 0, timestamp: deadlineStart }
      if (deadlineStart === todayStart) return { rank: 1, timestamp: deadlineStart }
      return { rank: 2, timestamp: deadlineStart }
    }
    activeTodoCount.value = active.length
    todayTodos.value = [...active]
      .sort((a, b) => {
        const urgencyDelta = urgency(a).rank - urgency(b).rank
        if (urgencyDelta !== 0) return urgencyDelta
        const aDeadline = urgency(a).timestamp
        const bDeadline = urgency(b).timestamp
        if (aDeadline !== bDeadline) return aDeadline - bDeadline
        if (Boolean(a.pinned) !== Boolean(b.pinned)) return a.pinned ? -1 : 1
        const scoreDelta = getPriorityScore(b, categoryById.get(b.category)).score - getPriorityScore(a, categoryById.get(a.category)).score
        if (scoreDelta !== 0) return scoreDelta
        return b.updated_at.localeCompare(a.updated_at)
      })
      .slice(0, 3)
    todoSummaryUnavailable.value = false
  } catch {
    if (requestId !== todoSummaryRequestId) return
    // 待办存储不可用时不阻断首页的计划和时间功能，但要明确告知用户，
    // 避免把读取故障伪装成“今天没有待办”。
    activeTodoCount.value = 0
    todayTodos.value = []
    todoSummaryUnavailable.value = true
  }
}

async function refreshTimeSummary(): Promise<void> {
  try {
    await appStore.refreshTodayData()
    timeSummaryUnavailable.value = false
  } catch (error) {
    timeSummaryUnavailable.value = true
    console.warn('Failed to refresh home time summary:', error)
  }
}

async function completeHomeTodo(todo: UnifiedTodo) {
  if (completingTodoId.value) return
  completingTodoId.value = todo.id
  try {
    await TodoService.complete(todo.id)
    await refreshTodoSummary()
  } catch (error) {
    notifyToast(error instanceof Error ? error.message : t('tasks.error.update'), 'error')
  } finally {
    completingTodoId.value = null
  }
}

async function addQuickTodo() {
  const title = quickTodoTitle.value.trim()
  if (!title || quickTodoSaving.value) return
  quickTodoSaving.value = true
  try {
    await TodoService.create({ title })
    quickTodoTitle.value = ''
    await refreshTodoSummary()
    notifyToast(t('home.quickTodoAdded'), 'success')
  } catch (error) {
    notifyToast(error instanceof Error ? error.message : t('tasks.error.create'), 'error')
  } finally {
    quickTodoSaving.value = false
  }
}

type TodoDeadlineState = 'overdue' | 'today' | 'upcoming' | 'invalid' | null

function getTodoDeadlineState(deadline?: string): TodoDeadlineState {
  if (!deadline) return null
  const date = parseStoredDate(deadline)
  if (Number.isNaN(date.getTime())) return 'invalid'
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const deadlineStart = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
  if (deadlineStart < todayStart) return 'overdue'
  if (deadlineStart === todayStart) return 'today'
  return 'upcoming'
}

function formatTodoDeadline(deadline?: string): string {
  if (!deadline) return t('home.noDeadline')
  const date = parseStoredDate(deadline)
  if (Number.isNaN(date.getTime())) return t('home.noDeadline')
  const formatted = date.toLocaleDateString(locale.value, { month: 'short', day: 'numeric' })
  const state = getTodoDeadlineState(deadline)
  if (state === 'overdue') return `${t('home.overdue')} · ${formatted}`
  if (state === 'today') return t('home.dueToday')
  return formatted
}

function formatTodoTime(todo: UnifiedTodo): string {
  const estimate = Number(todo.estimated_time ?? todo.time_estimate ?? 0)
  const spent = Number(todo.time_spent ?? 0)
  if (estimate <= 0 && spent <= 0) return ''
  return t('home.timeProgress', { spent, estimate: estimate > 0 ? estimate : '—' })
}

function openTodoRecord(todo: UnifiedTodo) {
  router.push({ path: '/records', query: { todo: todo.id } })
}

async function refreshEventPlanSummary() {
  const requestId = ++eventPlanSummaryRequestId
  eventPlanState.value = 'loading'
  try {
    const activePlans = await listPlanSummaries()
    if (requestId !== eventPlanSummaryRequestId) return
    eventPlans.value = activePlans
    eventPlanState.value = 'ready'
  } catch {
    if (requestId !== eventPlanSummaryRequestId) return
    eventPlans.value = []
    eventPlanState.value = 'unavailable'
  }
}

/** Serialize dashboard reads so a slow refresh cannot be overtaken by an older batch. */
async function refreshWorkspaceSummaries(): Promise<void> {
  if (summaryRefreshRunning) {
    summaryRefreshQueued = true
    return
  }
  summaryRefreshRunning = true
  try {
    do {
      summaryRefreshQueued = false
      await Promise.all([
        refreshTimeSummary(),
        refreshTodoSummary(),
        refreshEventPlanSummary(),
      ])
    } while (summaryRefreshQueued)
  } catch (error) {
    // Keep an unexpected coordinator failure recoverable; each module also
    // owns its normal unavailable state and retry affordance.
    console.warn('Failed to refresh home workspace summary:', error)
  } finally {
    summaryRefreshRunning = false
    workspaceSummaryReady.value = true
  }
}

function scheduleWorkspaceSummaryRefresh() {
  if (workspaceRefreshTimer !== null) return
  workspaceRefreshTimer = window.setTimeout(async () => {
    workspaceRefreshTimer = null
    await refreshWorkspaceSummaries()
  }, 80)
}

const stopWorkspaceListener = onWorkspaceChanged(scheduleWorkspaceSummaryRefresh)

const eventPlanTaskCount = computed(() => eventPlans.value.reduce((sum, plan) => sum + (plan.total_tasks || 0), 0))
const eventPlanCompletedCount = computed(() => eventPlans.value.reduce((sum, plan) => sum + (plan.completed_tasks || 0), 0))
const eventPlanProgress = computed(() => eventPlanTaskCount.value > 0
  ? Math.round((eventPlanCompletedCount.value / eventPlanTaskCount.value) * 100)
  : 0)
const eventPlanPreview = computed(() => eventPlans.value.slice(0, 3))
const eventPlanRemainingCount = computed(() => Math.max(0, eventPlans.value.length - eventPlanPreview.value.length))
const isEventPlanSnapshot = computed(() => planDataSource.value === 'cache' || planDataSource.value === 'mobile')
const eventPlanSnapshotLabel = computed(() => planDataSource.value === 'mobile'
  ? t('plans.mobileLocalTitle')
  : t('plans.cachedTitle'))
const todayRecordHours = computed(() => appStore.todayRecords.reduce((total, record) => {
  const duration = Number(record.duration)
  return Number.isFinite(duration) && duration >= 0 ? total + duration : total
}, 0))

const updateTime = () => {
  const now = new Date()
  const showSeconds = appStore.config.show_seconds

  const hours = now.getHours().toString().padStart(2, '0')
  const minutes = now.getMinutes().toString().padStart(2, '0')
  const seconds = now.getSeconds().toString().padStart(2, '0')

  if (appStore.config.use_24h) {
    currentTime.value = showSeconds ? `${hours}:${minutes}:${seconds}` : `${hours}:${minutes}`
  } else {
    let hours12 = now.getHours() % 12 || 12
    const ampm = now.getHours() < 12 ? 'AM' : 'PM'
    currentTime.value = showSeconds
      ? `${hours12}:${minutes}:${seconds} ${ampm}`
      : `${hours12}:${minutes} ${ampm}`
  }

  currentDate.value = now.toLocaleDateString(locale.value, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

watch(locale, updateTime)

const getProgressColor = (progress: number): string => {
  if (progress === 0) return 'var(--color-text-primary)'
  if (progress < 40) return 'var(--color-progress-low)'
  if (progress < 70) return 'var(--color-progress-medium)'
  if (progress < 90) return 'var(--color-progress-good)'
  return 'var(--color-progress-high)'
}

const stat = computed(() => appStore.todayStat)

// 打卡数据（响应式，来自 CheckinSystem）
const checkinStreak = computed(() => checkinState.currentStreak)
const hasCheckedInToday = computed(() => checkinState.hasCheckedInToday)

// 收件箱未读数量
const unreadCount = computed(() => EventSystem.getUnreadCount())

// 收件箱面板
const showInboxPanel = ref(false)
const inboxEntries = computed(() => EventSystem.getEventInbox().slice(0, 10))
const inboxPanel = ref<HTMLElement | null>(null)
const inboxButton = ref<HTMLButtonElement | null>(null)
const inboxCloseButton = ref<HTMLButtonElement | null>(null)

async function toggleInboxPanel() {
  showInboxPanel.value = !showInboxPanel.value
  if (showInboxPanel.value) {
    await nextTick()
    inboxCloseButton.value?.focus()
  }
}

function closeInboxPanel(restoreFocus = false) {
  showInboxPanel.value = false
  if (restoreFocus) {
    void nextTick().then(() => inboxButton.value?.focus())
  }
}

function handleInboxKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    closeInboxPanel(true)
    return
  }
  if (event.key !== 'Tab' || !inboxPanel.value) return
  const focusable = Array.from(inboxPanel.value.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  ))
  if (focusable.length === 0) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

function markInboxRead(entryId: string) {
  EventSystem.markAsRead(entryId)
}

function activateInboxEntry(event: KeyboardEvent, entryId: string) {
  if (event.key !== 'Enter' && event.key !== ' ') return
  event.preventDefault()
  markInboxRead(entryId)
}

function formatInboxTime(isoStr: string): string {
  const d = new Date(isoStr)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffH = Math.floor(diffMs / 3600000)
  const diffD = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return t('home.justNow')
  if (diffMin < 60) return `${diffMin}${t('home.minutesAgo')}`
  if (diffH < 24) return `${diffH}${t('home.hoursAgo')}`
  if (diffD < 7) return `${diffD}${t('home.daysAgo')}`
  return d.toLocaleDateString(locale.value, { month: 'short', day: 'numeric' })
}

// 今天是否可打卡（计划100%完成但还没打卡）
const canCheckinToday = computed(() => {
  if (hasCheckedInToday.value) return false
  return stat.value && stat.value.plan_exists && stat.value.progress >= 100
})

// 每个类别的进度百分比
function getTagProgress(tag: string): number {
  if (!stat.value || !stat.value.plan_exists) return 0
  const target = stat.value.target[tag] || 0
  const actual = stat.value.raw_stat[tag] || 0
  if (target <= 0) return 0
  return Math.min(100, Math.round((actual / target) * 100))
}

// 类别是否超出目标
function isTagExceeded(tag: string): boolean {
  if (!stat.value) return false
  return (stat.value.raw_stat[tag] || 0) > (stat.value.target[tag] || 0)
}

// 圆形进度条属性
const overallProgress = computed(() => stat.value?.progress || 0)
const circleRadius = 56
const circleCircumference = 2 * Math.PI * circleRadius
const overallDashOffset = computed(() => {
  const p = overallProgress.value
  return circleCircumference * (1 - p / 100)
})

onMounted(async () => {
  await refreshWorkspaceSummaries()
  updateTime()
  timer = window.setInterval(updateTime, 1000)
  // 每分钟刷新一次统计
  refreshTimer = window.setInterval(() => { void refreshWorkspaceSummaries() }, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (refreshTimer) clearInterval(refreshTimer)
  if (workspaceRefreshTimer !== null) clearTimeout(workspaceRefreshTimer)
  stopWorkspaceListener()
})
</script>

<template>
  <div class="home-view" :aria-busy="!workspaceSummaryReady">
    <header class="header">
      <!-- 收件箱入口 -->
      <div class="inbox-wrapper">
        <button ref="inboxButton" class="inbox-btn" type="button" :class="{ 'has-unread': unreadCount > 0 }" :aria-label="t('home.openInbox')" aria-haspopup="dialog" :aria-expanded="showInboxPanel" aria-controls="home-inbox-panel" @click="AudioManager.playSound('click'); toggleInboxPanel()">
          <Inbox :size="20" />
          <span v-if="unreadCount > 0" class="inbox-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </button>

      <!-- 收件箱下拉面板 -->
      <Transition name="inbox-dropdown">
        <div v-if="showInboxPanel" ref="inboxPanel" id="home-inbox-panel" class="inbox-panel" role="dialog" aria-modal="false" aria-labelledby="home-inbox-title" tabindex="-1" @keydown="handleInboxKeydown">
        <div class="inbox-panel-header">
          <h3 id="home-inbox-title" class="inbox-panel-title">{{ t('home.inbox') }}</h3>
          <div class="inbox-panel-actions">
            <button v-if="unreadCount > 0" type="button" class="inbox-action-btn" @click="EventSystem.markAllAsRead()">{{ t('home.markAllRead') }}</button>
            <button ref="inboxCloseButton" class="inbox-close-btn" type="button" :aria-label="t('home.closeInbox')" @click="closeInboxPanel()">
              <X :size="16" />
            </button>
          </div>
        </div>
        <div class="inbox-panel-body">
          <div v-if="inboxEntries.length === 0" class="inbox-empty">
            <EmptyState :icon="InboxIcon" :title="t('home.noMessages')" :description="t('home.notificationsHere')" />
          </div>
          <div v-else class="inbox-panel-list">
            <div
              v-for="entry in inboxEntries"
              :key="entry.id"
              class="inbox-panel-item"
              :class="{ unread: !entry.read }"
              role="button"
              tabindex="0"
              :aria-label="entry.title"
              @click="markInboxRead(entry.id)"
              @keydown="activateInboxEntry($event, entry.id)"
            >
              <span class="inbox-panel-icon"><component :is="getNotificationIcon(entry.type)" :size="16" :stroke-width="2" /></span>
              <div class="inbox-panel-content">
                <div class="inbox-panel-title-row">
                  <span class="inbox-panel-item-title">{{ entry.title }}</span>
                  <span v-if="!entry.read" class="inbox-unread-dot"></span>
                </div>
                <p class="inbox-panel-msg">{{ entry.message }}</p>
                <span class="inbox-panel-time">{{ formatInboxTime(entry.triggeredAt) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="inbox-panel-footer">
          <button type="button" class="inbox-panel-more" @click="closeInboxPanel(); router.push('/event-manager')">
            {{ t('home.viewAll') }}
            <ChevronRight :size="14" />
          </button>
        </div>
      </div>
    </Transition>
      <!-- 遮罩层 -->
      <Transition name="fade">
        <div v-if="showInboxPanel" class="inbox-overlay" @click="closeInboxPanel()"></div>
      </Transition>
      </div><!-- inbox-wrapper -->
    </header>

    <div class="main-content">
      <section class="clock-section">
        <div class="time-display">{{ currentTime }}</div>
        <div class="date-display">{{ currentDate }}</div>
        <div class="checkin-badges">
          <div class="checkin-badge" v-if="checkinStreak > 0">
            <Flame :size="18" class="flame-icon" />
            <span>{{ t('home.streak') }} <strong>{{ checkinStreak }}</strong> {{ t('home.days') }}</span>
          </div>
          <div class="checkin-reminder" v-if="!hasCheckedInToday && stat && stat.plan_exists && stat.progress >= 100">
            <Bell :size="14" />
            <span>{{ t('home.canCheckin') }}</span>
            <span class="red-dot"></span>
          </div>
        </div>
      </section>

      <section class="workflow-summary" :aria-label="t('home.workflowSummary')">
        <button class="workflow-summary-item" :class="{ 'is-unavailable': timeSummaryUnavailable, 'is-loading': !workspaceSummaryReady }" type="button" @click="router.push('/time')">
          <span class="workflow-summary-icon"><Clock3 :size="17" /><small>TH</small></span>
          <span class="workflow-summary-copy"><strong>{{ !workspaceSummaryReady || timeSummaryUnavailable ? '—' : hoursToHm(todayRecordHours, locale) }}</strong><small>{{ !workspaceSummaryReady ? t('home.summaryLoading') : timeSummaryUnavailable ? t('home.timeUnavailable') : t('home.timeModuleSummary') }}</small></span>
          <ChevronRight :size="16" />
        </button>
        <button class="workflow-summary-item" :class="{ 'is-unavailable': eventPlanState === 'unavailable', 'is-loading': !workspaceSummaryReady }" type="button" @click="router.push('/plans')">
          <span class="workflow-summary-icon"><ClipboardList :size="17" /><small>PH</small></span>
          <span class="workflow-summary-copy"><strong>{{ !workspaceSummaryReady || eventPlanState === 'unavailable' ? '—' : `${eventPlanCompletedCount}/${eventPlanTaskCount}` }}</strong><small>{{ !workspaceSummaryReady ? t('home.summaryLoading') : eventPlanState === 'unavailable' ? (mobilePlanRuntime ? t('home.eventPlansUnavailableMobile') : t('home.eventPlansUnavailable')) : t('home.planModuleSummary') }}</small></span>
          <ChevronRight :size="16" />
        </button>
        <button class="workflow-summary-item" :class="{ 'is-unavailable': todoSummaryUnavailable, 'is-loading': !workspaceSummaryReady }" type="button" @click="router.push('/tasks')">
          <span class="workflow-summary-icon"><ListTodo :size="17" /><small>TD</small></span>
          <span class="workflow-summary-copy"><strong>{{ !workspaceSummaryReady || todoSummaryUnavailable ? '—' : activeTodoCount }}</strong><small>{{ !workspaceSummaryReady ? t('home.summaryLoading') : todoSummaryUnavailable ? t('home.todosUnavailable') : t('home.todoModuleSummary') }}</small></span>
          <ChevronRight :size="16" />
        </button>
      </section>

      <!-- 总完成度环形图 + 分类进度条 -->
      <section class="stats-section">
        <div class="overview-grid">
        <section class="stats-card">
          <button type="button" class="stats-header-row stats-header-action" :aria-label="t('home.todayProgress')" @click="openDailyPlan">
            <span class="home-module-heading"><span class="home-module-code">TH</span><span><span class="home-module-label">{{ t('home.timeModuleSummary') }}</span><strong class="stats-title">{{ t('home.todayProgress') }}</strong></span></span>
            <span class="stats-date-label" v-if="stat?.plan_exists">{{ stat.plan_name }}</span>
            <ChevronRight :size="18" />
          </button>
          <div v-if="timeSummaryUnavailable" class="stats-unavailable" role="status" aria-live="polite">
            <span>{{ t('home.timeUnavailable') }}</span>
            <button type="button" @click="refreshTimeSummary">{{ t('home.retryTime') }}</button>
          </div>
          <div v-else-if="!workspaceSummaryReady" class="stats-loading" role="status" aria-live="polite">
            <span class="stats-loading-ring" aria-hidden="true"></span>
            <span>{{ t('home.summaryLoading') }}</span>
          </div>
          <div class="stats-content" v-else-if="stat && stat.plan_exists">
            <!-- 环形总完成度 -->
            <div class="overall-progress-ring">
              <svg class="ring-svg" viewBox="0 0 128 128">
                <circle
                  class="ring-bg"
                  cx="64" cy="64" :r="circleRadius"
                  fill="none" stroke-width="8"
                />
                <circle
                  class="ring-fg"
                  cx="64" cy="64" :r="circleRadius"
                  fill="none" stroke-width="8"
                  :stroke="getProgressColor(overallProgress)"
                  :stroke-dasharray="circleCircumference"
                  :stroke-dashoffset="overallDashOffset"
                  stroke-linecap="round"
                />
              </svg>
              <div class="ring-center">
                <span class="ring-value" :style="{ color: getProgressColor(overallProgress) }">{{ overallProgress }}%</span>
                <span class="ring-label">{{ t('home.overallProgress') }}</span>
              </div>
            </div>

            <!-- 各分类进度条 -->
            <div class="tag-bars">
              <div
                v-for="(target, tag) in stat.target"
                :key="tag"
                class="tag-bar-item"
                :class="{ 'is-bg-tag': tag === stat.bg_tag, 'is-exceeded': isTagExceeded(tag) }"
              >
                <div class="tag-bar-header">
                  <span class="tag-name">
                    <span class="tag-dot" :class="{ 'bg-dot': tag === stat.bg_tag }"></span>
                    {{ tag }}
                  </span>
                  <span class="tag-times">{{ hoursToHm(stat.raw_stat[tag] || 0, locale) }} <span class="tag-target">/ {{ hoursToHm(target, locale) }}</span></span>
                </div>
                <div class="tag-bar-track">
                  <div
                    class="tag-bar-fill"
                    :style="{
                      width: Math.min(100, getTagProgress(tag)) + '%',
                      backgroundColor: isTagExceeded(tag) ? 'var(--color-error)' : getProgressColor(getTagProgress(tag))
                    }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
          <div class="stats-content" v-else>
            <EmptyState
              :icon="ClipboardList"
              :title="t('home.noPlanData')"
              :description="t('home.createPlanForProgress')"
              :action-text="t('home.goToManage')"
              action-route="/plans"
            />
          </div>
        </section>
        <section class="event-overview-card">
          <button type="button" class="event-overview-header event-overview-header-action" @click="router.push('/plans')">
            <span class="home-module-heading"><span class="home-module-code">PH</span><span><span class="home-module-label">{{ t('home.planModuleSummary') }}</span><strong class="stats-title">{{ t('home.eventPlans') }}</strong></span></span><ChevronRight :size="18" />
          </button>
          <template v-if="eventPlanState === 'ready'">
            <strong class="event-overview-count">{{ eventPlans.length }}</strong>
            <span class="event-overview-label">{{ t('home.eventPlanCount') }}</span>
            <div class="event-overview-metrics"><span>{{ eventPlanCompletedCount }}/{{ eventPlanTaskCount }} {{ t('home.eventTasksDone') }}</span><span>{{ t('home.openPlanCenter') }}</span></div>
            <div class="event-overview-progress"><span>{{ eventPlanProgress }}%</span><div class="event-overview-progress-track"><i :style="{ width: `${eventPlanProgress}%` }" /></div></div>
            <div v-if="eventPlanPreview.length" class="event-plan-preview" :aria-label="t('home.eventPlans')">
              <button v-for="plan in eventPlanPreview" :key="plan.id" type="button" class="event-plan-preview-row" @click.stop="openEventPlan(plan)">
                <div class="event-plan-preview-copy">
                  <span class="event-plan-preview-name">{{ plan.name }}</span>
                  <span class="event-plan-preview-count">{{ plan.completed_tasks }}/{{ plan.total_tasks }}</span>
                </div>
                <div class="event-plan-preview-track"><i :style="{ width: `${plan.progress_percentage}%` }" /></div>
              </button>
              <span v-if="eventPlanRemainingCount" class="event-plan-preview-more">{{ t('home.moreActivePlans', { count: eventPlanRemainingCount }) }}</span>
            </div>
            <span v-if="isEventPlanSnapshot" class="event-overview-snapshot">{{ eventPlanSnapshotLabel }}</span>
          </template>
          <span v-else-if="eventPlanState === 'loading'" class="event-overview-muted">{{ t('home.eventPlansLoading') }}</span>
          <div v-else class="event-overview-unavailable">
            <span class="event-overview-muted">{{ mobilePlanRuntime ? t('home.eventPlansUnavailableMobile') : t('home.eventPlansUnavailable') }}</span>
            <button v-if="!mobilePlanRuntime" type="button" class="event-overview-retry" @click="refreshEventPlanSummary">
              {{ t('home.retryEventPlans') }}
            </button>
          </div>
        </section>
        </div>
      </section>

      <section class="today-todos-card theme-card">
        <div class="today-todos-header">
          <div>
            <p class="today-todos-eyebrow"><span class="home-module-code">TD</span>{{ t('home.todayTodosEyebrow') }}</p>
            <h2 class="stats-title">{{ t('home.todayTodos') }}</h2>
          </div>
          <button type="button" class="today-todos-link" @click="router.push('/tasks')">
            {{ t('home.viewTodos') }} <ChevronRight :size="16" />
          </button>
        </div>
        <form class="today-todo-capture" @submit.prevent="addQuickTodo">
          <input v-model="quickTodoTitle" type="text" :placeholder="t('home.quickTodoPlaceholder')" :disabled="quickTodoSaving" :aria-label="t('home.quickTodoPlaceholder')" />
          <button type="submit" :disabled="quickTodoSaving || !quickTodoTitle.trim()"><Plus :size="14" /> {{ t('home.quickAddTodo') }}</button>
        </form>
        <div v-if="todoSummaryUnavailable" class="today-todos-unavailable" role="status" aria-live="polite">
          <span>{{ t('home.todosUnavailable') }}</span>
          <button type="button" @click="refreshTodoSummary">{{ t('home.retryTodos') }}</button>
        </div>
        <div v-else-if="!workspaceSummaryReady" class="today-todos-loading" role="status" aria-live="polite">
          <span class="today-todos-loading-bar" aria-hidden="true"></span>
          <span>{{ t('home.summaryLoading') }}</span>
        </div>
        <div v-else-if="todayTodos.length" class="today-todos-list">
          <div v-for="todo in todayTodos" :key="todo.id" class="today-todo-row">
            <button type="button" class="today-todo-complete" :disabled="completingTodoId === todo.id" :aria-label="t('tasks.completeLabelFor', { title: todo.title })" @click="completeHomeTodo(todo)">
              <Check v-if="completingTodoId === todo.id" :size="13" />
            </button>
            <button type="button" class="today-todo-main" @click="router.push({ path: '/tasks', query: { todo: todo.id } })">
              <span class="today-todo-copy">
                <span class="today-todo-title">{{ todo.title }}</span>
                <span class="today-todo-meta">
                  <span
                    v-if="todo.deadline"
                    class="today-todo-deadline"
                    :class="{ 'is-overdue': getTodoDeadlineState(todo.deadline) === 'overdue', 'is-today': getTodoDeadlineState(todo.deadline) === 'today' }"
                  >{{ formatTodoDeadline(todo.deadline) }}</span>
                  <span v-if="formatTodoTime(todo)" class="today-todo-time">{{ formatTodoTime(todo) }}</span>
                </span>
              </span>
            </button>
            <button class="today-todo-record" type="button" :aria-label="t('home.recordTodoTime')" :title="t('home.recordTodoTime')" @click.stop="openTodoRecord(todo)">
              <Clock3 :size="14" />
            </button>
          </div>
          <p v-if="activeTodoCount > todayTodos.length" class="today-todos-more">
            {{ t('home.moreTodos', { count: activeTodoCount - todayTodos.length }) }}
          </p>
        </div>
        <EmptyState v-else :icon="ListTodo" :title="t('home.noTodos')" :description="t('home.createTodoHint')" :action-text="t('home.openTodoCenter')" action-route="/tasks" />
      </section>

      <nav class="home-quick-actions" :aria-label="t('nav.checkin')">
        <button class="home-checkin-action" type="button" @click="AudioManager.playSound('click'); router.push('/checkin')">
          <CheckCircle :size="18" />
          <span>{{ t('nav.checkin') }}</span>
          <span v-if="canCheckinToday && !hasCheckedInToday" class="home-checkin-dot" aria-hidden="true"></span>
        </button>
      </nav>
    </div>

    <footer class="footer">
      <p>{{ t('home.footer') }}</p>
    </footer>
  </div>
</template>

<style scoped>
.home-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
}

.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: var(--spacing-md) 0;
  position: relative;
}

.workflow-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 0 auto 20px; width: min(860px, 100%); }
.workflow-summary-item { display: flex; align-items: center; gap: 10px; min-width: 0; border: 1px solid var(--color-border); border-radius: var(--radius-lg, 14px); padding: 12px 13px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; text-align: left; transition: transform var(--transition-fast), border-color var(--transition-fast), background var(--transition-fast); }
.workflow-summary-item:hover { border-color: var(--color-border-hover); background: var(--color-bg-tertiary); transform: translateY(-1px); }
.workflow-summary-item.is-unavailable { border-style: dashed; }
.workflow-summary-item.is-unavailable .workflow-summary-copy strong { color: var(--color-text-tertiary); }
.workflow-summary-item.is-loading { cursor: wait; }
.workflow-summary-item.is-loading .workflow-summary-icon { opacity: .6; }
.workflow-summary-icon { position: relative; display: grid; place-items: center; flex: 0 0 auto; width: 30px; height: 30px; border-radius: 9px; color: var(--color-primary); background: var(--color-primary-muted); }
.workflow-summary-icon small { position: absolute; right: -5px; bottom: -5px; border: 1px solid var(--color-bg-secondary); border-radius: 4px; padding: 1px 2px; color: var(--color-text-primary); background: var(--color-bg-elevated); font-family: var(--font-mono, ui-monospace, monospace); font-size: 7px; font-weight: 800; line-height: 1; }
.workflow-summary-copy { display: grid; gap: 2px; min-width: 0; flex: 1; }
.workflow-summary-copy strong { color: var(--color-text-primary); font-size: 15px; font-variant-numeric: tabular-nums; }
.workflow-summary-copy small { overflow: hidden; color: var(--color-text-tertiary); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.home-module-heading { display: inline-flex; align-items: center; gap: 9px; min-width: 0; }
.home-module-heading > span:last-child { display: grid; min-width: 0; gap: 2px; }
.home-module-label { overflow: hidden; color: var(--color-text-tertiary); font-size: 10px; font-weight: 700; letter-spacing: .06em; text-overflow: ellipsis; text-transform: uppercase; white-space: nowrap; }
.home-module-code { display: inline-grid; place-items: center; min-width: 26px; height: 20px; box-sizing: border-box; border: 1px solid var(--color-border); border-radius: 6px; padding: 0 5px; color: var(--color-primary); background: var(--color-primary-muted); font-family: var(--font-mono, ui-monospace, monospace); font-size: 10px; font-weight: 800; letter-spacing: .04em; line-height: 1; }
.today-todos-eyebrow .home-module-code { margin-right: 6px; vertical-align: 1px; }
@media (prefers-reduced-motion: reduce) { .workflow-summary-item { transition: none; } }
@media (max-width: 680px) { .workflow-summary { grid-template-columns: 1fr; } }

/* 收件箱容器 */
.inbox-wrapper {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
}

/* 收件箱按钮 */
.inbox-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.inbox-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border-color: var(--color-border-hover);
}

.inbox-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: var(--color-error);
  color: white;
  font-size: 0.625rem;
  font-weight: 700;
  border-radius: 9px;
  line-height: 1;
}

.inbox-btn.has-unread {
  animation: inboxShake 4s ease-in-out infinite;
}

@keyframes inboxShake {
  0%, 90%, 100% { transform: translateY(-50%) rotate(0deg); }
  92% { transform: translateY(-50%) rotate(-5deg); }
  94% { transform: translateY(-50%) rotate(5deg); }
  96% { transform: translateY(-50%) rotate(-3deg); }
  98% { transform: translateY(-50%) rotate(3deg); }
}

/* 收件箱下拉面板 */
.inbox-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: min(360px, calc(100vw - 32px));
  max-width: calc(100vw - 32px);
  max-height: 480px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.inbox-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.inbox-panel-title {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0;
}

.inbox-panel-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.inbox-action-btn {
  padding: 2px 8px;
  border: none;
  background: transparent;
  color: var(--color-primary);
  font-size: 0.75rem;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.inbox-action-btn:hover {
  background: var(--color-bg-secondary);
}

.inbox-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.inbox-close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.inbox-panel-body {
  flex: 1;
  overflow-y: auto;
  max-height: 340px;
}

.inbox-empty {
  padding: var(--spacing-lg);
}

.inbox-panel-list {
  display: flex;
  flex-direction: column;
}

.inbox-panel-item {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  cursor: pointer;
  transition: background var(--transition-fast);
  border-bottom: 1px solid var(--color-border);
}

.inbox-panel-item:last-child {
  border-bottom: none;
}

.inbox-panel-item:hover {
  background: var(--color-bg-secondary);
}

.inbox-panel-item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.inbox-panel-item.unread {
  background: rgba(var(--color-primary-rgb, 99, 102, 241), 0.04);
}

.inbox-panel-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  width: 28px;
  text-align: center;
  line-height: 1.4;
}

.inbox-panel-content {
  flex: 1;
  min-width: 0;
}

.inbox-panel-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.inbox-panel-item-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.inbox-unread-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
}

.inbox-panel-msg {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin: 2px 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inbox-panel-time {
  font-size: 0.6875rem;
  color: var(--color-text-tertiary);
}

.inbox-panel-footer {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  text-align: center;
}

.inbox-panel-more {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: var(--spacing-xs) var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--color-primary);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.inbox-panel-more:hover {
  background: var(--color-bg-secondary);
}

/* 收件箱动画 */
.inbox-dropdown-enter-active,
.inbox-dropdown-leave-active {
  transition: all 0.2s ease;
}
.inbox-dropdown-enter-from,
.inbox-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.inbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2xl);
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.clock-section {
  text-align: center;
}

.time-display {
  font-size: 4rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  line-height: 1;
}

.date-display {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-sm);
}

.checkin-badges {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.checkin-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.15) 0%, rgba(255, 215, 0, 0.15) 100%);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  color: var(--color-text-primary);
  animation: badgePulse 3s ease-in-out infinite;
}

.checkin-badge strong {
  color: #ff8c00;
  font-weight: 700;
  font-size: 1rem;
  font-family: var(--font-mono);
}

.flame-icon {
  color: #ff8c00;
  animation: flameFlicker 1.5s ease-in-out infinite;
}

/* 打卡提醒红点 */
.checkin-reminder {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  color: var(--color-error);
  cursor: pointer;
  animation: reminderPulse 2s ease-in-out infinite;
}

.red-dot {
  width: 6px;
  height: 6px;
  background: var(--color-error);
  border-radius: 50%;
  animation: dotPulse 1.5s ease-in-out infinite;
}

@keyframes reminderPulse {
  0%, 100% { box-shadow: 0 0 0 rgba(239, 68, 68, 0); }
  50% { box-shadow: 0 0 12px rgba(239, 68, 68, 0.2); }
}

@keyframes dotPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.5); }
}

@keyframes badgePulse {
  0%, 100% { box-shadow: 0 0 0 rgba(255, 215, 0, 0); }
  50% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.2); }
}

@keyframes flameFlicker {
  0%, 100% { transform: scale(1) rotate(-2deg); }
  50% { transform: scale(1.1) rotate(2deg); }
}

.stats-section {
  width: 100%;
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(240px, .55fr);
  gap: var(--spacing-md);
}

.stats-card {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  transition: all var(--transition-fast);
}

.stats-card:hover {
  border-color: var(--color-border-hover);
  background: var(--color-bg-secondary);
  box-shadow: 0 0 0 2px var(--color-primary-muted);
}

.stats-header-row { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: var(--spacing-sm); color: var(--color-text-tertiary); }
.stats-header-action { border: 0; padding: 0; background: transparent; cursor: pointer; font: inherit; text-align: left; }
.stats-header-action:hover, .stats-header-action:focus-visible { color: var(--color-text-primary); outline: 0; }
.stats-header-action svg { flex: 0 0 auto; color: var(--color-primary); }

.event-overview-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 100%;
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  background: var(--color-bg-secondary);
  text-align: left;
  transition: all var(--transition-fast);
}

.event-overview-card:hover {
  border-color: var(--color-border-hover);
  background: var(--color-bg-secondary);
  box-shadow: 0 0 0 2px var(--color-primary-muted);
}

.event-overview-header { display: flex; align-items: center; justify-content: space-between; width: 100%; color: var(--color-text-tertiary); }
.event-overview-header-action { border: 0; padding: 0; background: transparent; cursor: pointer; font: inherit; text-align: left; }
.event-overview-header-action:hover, .event-overview-header-action:focus-visible { color: var(--color-text-primary); outline: 0; }
.event-overview-header svg { color: var(--color-primary); }
.event-overview-count { margin-top: var(--spacing-xl); color: var(--color-primary); font-size: 2.4rem; line-height: 1; }
.event-overview-label { margin-top: 7px; color: var(--color-text-secondary); font-size: 13px; }
.event-overview-metrics { display: flex; flex-wrap: wrap; gap: 6px 12px; margin-top: auto; padding-top: var(--spacing-lg); color: var(--color-text-tertiary); font-size: 12px; }
.event-overview-progress { display: flex; align-items: center; gap: 8px; margin-top: 12px; color: var(--color-primary); font-size: 12px; font-variant-numeric: tabular-nums; }
.event-overview-progress-track { height: 6px; flex: 1; overflow: hidden; border-radius: 999px; background: var(--color-bg-elevated); }
.event-overview-progress-track i { display: block; height: 100%; border-radius: inherit; background: var(--color-primary); transition: width .25s ease; }
.event-plan-preview { display: grid; gap: 8px; width: 100%; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--color-border); }
.event-plan-preview-row { display: grid; gap: 5px; min-width: 0; width: 100%; border: 0; padding: 0; color: inherit; background: transparent; cursor: pointer; text-align: left; }
.event-plan-preview-row:hover .event-plan-preview-name, .event-plan-preview-row:focus-visible .event-plan-preview-name { color: var(--color-primary); }
.event-plan-preview-copy { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-width: 0; color: var(--color-text-secondary); font-size: 11px; }
.event-plan-preview-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-plan-preview-count { flex: 0 0 auto; color: var(--color-text-tertiary); font-variant-numeric: tabular-nums; }
.event-plan-preview-track { height: 4px; overflow: hidden; border-radius: 999px; background: var(--color-bg-elevated); }
.event-plan-preview-track i { display: block; height: 100%; border-radius: inherit; background: var(--color-primary); opacity: .72; transition: width .25s ease; }
.event-plan-preview-more { color: var(--color-text-tertiary); font-size: 11px; }
.event-overview-snapshot { margin-top: 7px; color: var(--color-warning, var(--color-text-tertiary)); font-size: 11px; }
.event-overview-muted { margin-top: auto; padding-top: var(--spacing-xl); color: var(--color-text-tertiary); font-size: 13px; }
.event-overview-unavailable { display: grid; align-content: start; gap: 12px; width: 100%; margin-top: auto; }
.event-overview-unavailable .event-overview-muted { margin-top: 0; padding-top: var(--spacing-xl); }
.event-overview-retry { justify-self: start; border: 1px solid var(--color-border); border-radius: 9px; padding: 7px 10px; color: var(--color-primary); background: var(--color-primary-muted); cursor: pointer; font: inherit; font-size: 12px; }
.event-overview-retry:hover { border-color: var(--color-border-hover); }
.event-overview-retry:disabled { cursor: wait; opacity: .6; }

.today-todos-card {
  margin-top: var(--spacing-md);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-secondary);
}

.today-todos-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--spacing-md); }
.today-todos-eyebrow { margin: 0 0 4px; color: var(--color-primary); font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.today-todos-link { display: inline-flex; align-items: center; gap: 4px; padding: 5px 0; color: var(--color-primary); font-size: 12px; }
.today-todo-capture { display: flex; gap: 8px; margin-top: var(--spacing-md); }
.today-todo-capture input { min-width: 0; flex: 1; border: 1px solid var(--color-border); border-radius: 9px; padding: 8px 10px; color: var(--color-text-primary); background: var(--color-bg); font: inherit; font-size: 12px; }
.today-todo-capture input:focus-visible { border-color: var(--color-primary); outline: 2px solid color-mix(in srgb, var(--color-primary) 25%, transparent); outline-offset: 1px; }
.today-todo-capture button { display: inline-flex; align-items: center; justify-content: center; gap: 5px; flex: 0 0 auto; border: 1px solid var(--color-primary); border-radius: 9px; padding: 8px 11px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; font: inherit; font-size: 12px; font-weight: 650; }
.today-todo-capture button:disabled { cursor: not-allowed; opacity: .5; }
.today-todos-list { display: grid; gap: 6px; margin-top: var(--spacing-md); }
.today-todos-unavailable { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: var(--spacing-md); padding: 12px; border: 1px solid color-mix(in srgb, var(--color-error) 42%, var(--color-border)); border-radius: 10px; color: var(--color-text-secondary); background: var(--color-bg); font-size: 12px; }
.today-todos-unavailable button { flex: 0 0 auto; border: 1px solid var(--color-border); border-radius: 8px; padding: 6px 9px; color: var(--color-primary); background: var(--color-bg-secondary); cursor: pointer; font: inherit; font-size: 11px; font-weight: 650; }
.today-todos-unavailable button:hover, .today-todos-unavailable button:focus-visible { border-color: var(--color-primary); outline: 0; }
.today-todo-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 9px; width: 100%; padding: 10px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-primary); background: var(--color-bg); text-align: left; transition: border-color var(--transition-fast), transform var(--transition-fast); }
.today-todo-row:hover { border-color: var(--color-primary); transform: translateX(2px); }
.today-todo-complete { display: grid; place-items: center; width: 20px; height: 20px; border: 2px solid var(--color-primary); border-radius: 50%; color: var(--color-primary); background: transparent; cursor: pointer; transition: color var(--transition-fast), background-color var(--transition-fast), transform var(--transition-fast); }
.today-todo-complete:hover, .today-todo-complete:focus-visible { color: var(--color-button-text); background: var(--color-primary); outline: 0; transform: scale(1.06); }
.today-todo-complete:disabled { color: var(--color-primary); background: var(--color-primary-muted); cursor: wait; opacity: .75; }
.today-todo-main { display: flex; min-width: 0; border: 0; padding: 0; color: inherit; background: transparent; cursor: pointer; text-align: left; }
.today-todo-copy { display: grid; min-width: 0; gap: 3px; }
.today-todo-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.today-todo-meta { display: flex; flex-wrap: wrap; gap: 8px; color: var(--color-text-tertiary); font-size: 11px; }
.today-todo-deadline, .today-todo-time { white-space: nowrap; }
.today-todo-deadline.is-overdue { color: var(--color-error); font-weight: 700; }
.today-todo-deadline.is-today { color: var(--color-primary); font-weight: 700; }
.today-todo-record { display: grid; place-items: center; width: 27px; height: 27px; border: 1px solid var(--color-border); border-radius: 8px; color: var(--color-text-tertiary); background: var(--color-bg-secondary); cursor: pointer; }
.today-todo-record:hover, .today-todo-record:focus-visible { border-color: var(--color-primary); color: var(--color-primary); outline: 0; }
.today-todos-more { margin: 3px 0 0 29px; color: var(--color-text-tertiary); font-size: 11px; }

@media (max-width: 760px) {
  .overview-grid { grid-template-columns: 1fr; }
  .event-overview-card { min-height: 180px; }
  .today-todos-header { align-items: center; }
  .today-todo-capture { flex-direction: column; }
  .today-todo-capture button { width: 100%; }
  .today-todo-deadline { display: none; }
  .today-todos-link { min-height: 40px; }
  .today-todo-complete { width: 32px; height: 32px; }
  .today-todo-record { width: 40px; height: 40px; }
}

/* 平板横向工作台：保留桌面层级，避免 761–899px 被窄单列容器浪费。 */
@media (min-width: 761px) and (max-width: 899px) {
  .home-view { padding: 18px 24px; }
  .main-content {
    display: grid;
    grid-template-columns: minmax(190px, .46fr) minmax(0, 1.54fr);
    align-items: stretch;
    justify-content: flex-start;
    max-width: 900px;
    gap: 20px;
  }
  .clock-section {
    grid-column: 1;
    grid-row: 1 / span 4;
    align-self: start;
    position: sticky;
    top: 18px;
    padding: 22px 16px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    background: linear-gradient(155deg, var(--color-bg-secondary), var(--color-bg));
    text-align: left;
  }
  .checkin-badges { justify-content: flex-start; }
  .workflow-summary,
  .stats-section,
  .today-todos-card,
  .home-quick-actions { grid-column: 2; width: 100%; }
  .workflow-summary { margin-bottom: 0; }
}

.stats-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.stats-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin: 0;
}

.stats-date-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  padding: 2px 8px;
  background: var(--color-bg);
  border-radius: var(--radius-full);
}

.stats-content {
  padding: var(--spacing-sm) 0;
}
.stats-unavailable { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 120px; padding: var(--spacing-md); border: 1px solid color-mix(in srgb, var(--color-error) 42%, var(--color-border)); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg); font-size: 12px; }
.stats-unavailable button { flex: 0 0 auto; border: 1px solid var(--color-border); border-radius: 8px; padding: 6px 9px; color: var(--color-primary); background: var(--color-bg-secondary); cursor: pointer; font: inherit; font-size: 11px; font-weight: 650; }
.stats-unavailable button:hover, .stats-unavailable button:focus-visible { border-color: var(--color-primary); outline: 0; }
.stats-loading { display: grid; place-items: center; gap: 10px; min-height: 168px; color: var(--color-text-tertiary); font-size: 12px; }
.stats-loading-ring { width: 24px; height: 24px; border: 2px solid var(--color-primary-muted); border-top-color: var(--color-primary); border-radius: 50%; animation: home-spin .8s linear infinite; }
.today-todos-loading { display: flex; align-items: center; gap: 10px; margin-top: var(--spacing-md); min-height: 58px; color: var(--color-text-tertiary); font-size: 12px; }
.today-todos-loading-bar { width: 100px; height: 8px; border-radius: 999px; background: var(--color-primary-muted); animation: home-pulse 1.2s ease-in-out infinite; }
@keyframes home-spin { to { transform: rotate(360deg); } }
@keyframes home-pulse { 50% { opacity: .45; } }
@media (prefers-reduced-motion: reduce) { .stats-loading-ring, .today-todos-loading-bar { animation: none; } }

/* 环形总完成度 */
.overall-progress-ring {
  position: relative;
  width: 128px;
  height: 128px;
  margin: 0 auto var(--spacing-lg);
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  stroke: var(--color-bg-tertiary);
}

.ring-fg {
  transition: stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.3s ease;
}

.ring-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.ring-value {
  font-size: 1.75rem;
  font-weight: 800;
  font-family: var(--font-mono);
  line-height: 1;
}

.ring-label {
  font-size: 0.6875rem;
  color: var(--color-text-tertiary);
}

/* 分类进度条 */
.tag-bars {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.tag-bar-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tag-bar-item.is-exceeded .tag-bar-header .tag-name {
  color: var(--color-error);
}

.tag-bar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tag-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.tag-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  background: var(--color-primary);
  flex-shrink: 0;
}

.tag-dot.bg-dot {
  background: var(--color-success);
  border-radius: 50%;
}

.tag-times {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

.tag-target {
  color: var(--color-text-tertiary);
}

.tag-bar-track {
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.tag-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s ease;
  min-width: 0;
}

.empty-hint {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  padding: var(--spacing-md) 0;
}

.home-quick-actions {
  display: flex;
  justify-content: flex-start;
  width: 100%;
}

.home-checkin-action {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  padding: 10px 14px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.home-checkin-action:hover {
  background: var(--color-bg-secondary);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-muted);
  transform: translateY(-2px);
}

.home-checkin-action:active {
  transform: translateY(0) scale(0.96);
}

.home-checkin-dot {
  position: absolute;
  top: 6px;
  right: 7px;
  width: 8px;
  height: 8px;
  background: var(--color-error);
  border-radius: 50%;
  animation: dotPulse 1.5s ease-in-out infinite;
}

.footer {
  text-align: center;
  padding: var(--spacing-md) 0;
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
}

/* 宽屏控制台：桌面端使用可扫描的横向分区，不把内容压缩在移动端宽度内。 */
@media (min-width: 900px) {
  .home-view { padding: 20px 32px; }
  .main-content {
    display: grid;
    grid-template-columns: minmax(220px, .58fr) minmax(0, 1.42fr);
    align-items: start;
    align-content: start;
    justify-content: stretch;
    max-width: 1180px;
    gap: 24px;
  }
  .clock-section {
    grid-column: 1;
    grid-row: 1 / span 4;
    position: sticky;
    top: 24px;
    align-self: start;
    padding: 28px 20px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    background: linear-gradient(155deg, var(--color-bg-secondary), var(--color-bg));
    text-align: left;
  }
  .checkin-badges { justify-content: flex-start; }
  .workflow-summary,
  .stats-section,
  .today-todos-card,
  .home-quick-actions { grid-column: 2; width: 100%; }
  .workflow-summary { margin-bottom: 0; }
  .overview-grid { grid-template-columns: minmax(0, 1.55fr) minmax(300px, .75fr); }
  .stats-content {
    display: grid;
    grid-template-columns: minmax(150px, 190px) minmax(0, 1fr);
    align-items: center;
    gap: 24px;
  }
  .overall-progress-ring { margin: 0 auto; }
}
</style>
