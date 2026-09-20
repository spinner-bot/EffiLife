<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { hoursToHm } from '@/services/dataService'
import { ClipboardList, Calendar, Settings, Flame, Inbox, Bell, CheckCircle, ChevronRight, X } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import { EventSystem } from '@/audio'
import { checkinState } from '@/data'

const router = useRouter()
const appStore = useAppStore()

const currentTime = ref('')
const currentDate = ref('')
let timer: number | null = null
let refreshTimer: number | null = null

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

  currentDate.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

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

function toggleInboxPanel() {
  showInboxPanel.value = !showInboxPanel.value
}

function closeInboxPanel() {
  showInboxPanel.value = false
}

function markInboxRead(entryId: string) {
  EventSystem.markAsRead(entryId)
}

function formatInboxTime(isoStr: string): string {
  const d = new Date(isoStr)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffH = Math.floor(diffMs / 3600000)
  const diffD = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffH < 24) return `${diffH}小时前`
  if (diffD < 7) return `${diffD}天前`
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
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
  await appStore.init()
  updateTime()
  timer = window.setInterval(updateTime, 1000)
  // 每分钟刷新一次统计
  refreshTimer = window.setInterval(() => {
    appStore.refreshTodayData()
  }, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div class="home-view">
    <header class="header">
      <h1 class="logo">浪兮效率时钟</h1>
      <!-- 收件箱入口 -->
      <div class="inbox-wrapper">
        <button class="inbox-btn" :class="{ 'has-unread': unreadCount > 0 }" @click="AudioManager.playSound('click'); toggleInboxPanel()">
          <Inbox :size="20" />
          <span v-if="unreadCount > 0" class="inbox-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </button>

      <!-- 收件箱下拉面板 -->
      <Transition name="inbox-dropdown">
        <div v-if="showInboxPanel" class="inbox-panel">
        <div class="inbox-panel-header">
          <h3 class="inbox-panel-title">收件箱</h3>
          <div class="inbox-panel-actions">
            <button v-if="unreadCount > 0" class="inbox-action-btn" @click="EventSystem.markAllAsRead()">全部已读</button>
            <button class="inbox-close-btn" @click="closeInboxPanel()">
              <X :size="16" />
            </button>
          </div>
        </div>
        <div class="inbox-panel-body">
          <div v-if="inboxEntries.length === 0" class="inbox-empty">
            <Inbox :size="32" class="inbox-empty-icon" />
            <p>暂无消息</p>
          </div>
          <div v-else class="inbox-panel-list">
            <div
              v-for="entry in inboxEntries"
              :key="entry.id"
              class="inbox-panel-item"
              :class="{ unread: !entry.read }"
              @click="markInboxRead(entry.id)"
            >
              <span class="inbox-panel-icon">{{ entry.icon || '🔔' }}</span>
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
          <button class="inbox-panel-more" @click="closeInboxPanel(); router.push('/event-manager')">
            查看全部
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

    <main class="main-content">
      <section class="clock-section">
        <div class="time-display">{{ currentTime }}</div>
        <div class="date-display">{{ currentDate }}</div>
        <div class="checkin-badges">
          <div class="checkin-badge" v-if="checkinStreak > 0">
            <Flame :size="18" class="flame-icon" />
            <span>连续 <strong>{{ checkinStreak }}</strong> 天</span>
          </div>
          <div class="checkin-reminder" v-if="!hasCheckedInToday && stat && stat.plan_exists && stat.progress >= 100">
            <Bell :size="14" />
            <span>可打卡</span>
            <span class="red-dot"></span>
          </div>
        </div>
      </section>

      <!-- 总完成度环形图 + 分类进度条 -->
      <section class="stats-section">
        <div class="stats-card" @click="router.push('/plan')">
          <div class="stats-header-row">
            <h2 class="stats-title">今日进度</h2>
            <span class="stats-date-label" v-if="stat?.plan_exists">{{ stat.plan_name }}</span>
          </div>
          <div class="stats-content" v-if="stat && stat.plan_exists">
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
                <span class="ring-label">总完成度</span>
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
                  <span class="tag-times">{{ hoursToHm(stat.raw_stat[tag] || 0) }} <span class="tag-target">/ {{ hoursToHm(target) }}</span></span>
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
            <p class="empty-hint">暂无计划数据，点击前往管理</p>
          </div>
        </div>
      </section>

      <nav class="nav-buttons">
        <button class="nav-btn" @click="AudioManager.playSound('click'); router.push('/plan')">
          <ClipboardList :size="22" />
          <span>计划</span>
        </button>
        <button class="nav-btn" @click="AudioManager.playSound('click'); router.push('/calendar')">
          <Calendar :size="22" />
          <span>日历</span>
        </button>
        <button class="nav-btn checkin-nav" @click="AudioManager.playSound('click'); router.push('/checkin')">
          <CheckCircle :size="22" />
          <span>打卡</span>
          <span v-if="canCheckinToday && !hasCheckedInToday" class="nav-red-dot"></span>
        </button>
        <div class="nav-btn placeholder" aria-disabled="true">
          <span class="nav-placeholder-icon">···</span>
          <span class="nav-placeholder-text">敬请期待</span>
        </div>
        <button class="nav-btn" @click="AudioManager.playSound('click'); router.push('/settings')">
          <Settings :size="22" />
          <span>设置</span>
        </button>
      </nav>
    </main>

    <footer class="footer">
      <p>浪兮效率 | 专注高效生活</p>
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
  justify-content: center;
  padding: var(--spacing-md) 0;
  position: relative;
}

.logo {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

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
  width: 360px;
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
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-tertiary);
}

.inbox-empty-icon {
  opacity: 0.3;
  margin-bottom: var(--spacing-sm);
}

.inbox-empty p {
  margin: var(--spacing-xs) 0;
  font-size: 0.875rem;
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

.stats-card {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.stats-card:hover {
  border-color: var(--color-border-hover);
  background: var(--color-bg-tertiary);
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
  padding: var(--spacing-lg) 0;
}

.nav-buttons {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-sm);
  width: 100%;
}

.nav-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
}

.nav-btn:active {
  transform: translateY(0);
}

.checkin-nav {
  position: relative;
}

.nav-btn.placeholder {
  cursor: default;
  opacity: 0.4;
  border-style: dashed;
}

.nav-btn.placeholder:hover {
  transform: none;
  background: var(--color-bg-secondary);
  border-color: var(--color-border);
}

.nav-placeholder-icon {
  font-size: 1.25rem;
  letter-spacing: 2px;
  color: var(--color-text-tertiary);
  line-height: 1;
}

.nav-placeholder-text {
  font-size: 0.6875rem;
  color: var(--color-text-tertiary);
}

.nav-red-dot {
  position: absolute;
  top: 6px;
  right: 6px;
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
</style>
