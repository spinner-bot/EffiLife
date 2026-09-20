<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Flame, Calendar, Trophy, TrendingUp, Check, BarChart3 } from 'lucide-vue-next'
import { CheckinSystem, checkinState } from '@/data'
import { useAppStore } from '@/stores/app'
import { AudioManager } from '@/audio'
import { EventSystem } from '@/audio'
import ContributionHeatmap from '@/components/ContributionHeatmap.vue'

const router = useRouter()
const appStore = useAppStore()

const checkinData = computed(() => CheckinSystem.getData())
const hasCheckedInToday = computed(() => checkinState.hasCheckedInToday)
const currentStreak = computed(() => checkinState.currentStreak)
const longestStreak = computed(() => checkinState.longestStreak)
const totalCheckins = computed(() => checkinState.totalCheckins)

// 是否可以打卡：今天未打卡且有已完成的计划
const canCheckinToday = computed(() => {
  if (hasCheckedInToday.value) return false
  const stat = appStore.todayStat
  return stat && stat.plan_exists && stat.progress >= 100
})

const planName = computed(() => appStore.todayStat?.plan_name || '')

// 动画阶段
const phase = ref<'idle' | 'animating' | 'done'>('idle')
const displayStreak = ref(0)
const showBurst = ref(false)

// 打卡操作
function doCheckin() {
  if (!canCheckinToday.value || phase.value !== 'idle') return

  AudioManager.playSound('achievement')

  const result = CheckinSystem.checkin(planName.value, 100)
  if (result === null) return

  phase.value = 'animating'
  const startStreak = result - 1
  displayStreak.value = startStreak

  const duration = 1200
  const startTime = Date.now()

  function animate() {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    displayStreak.value = Math.round(startStreak + (result - startStreak) * eased)

    if (progress < 1) {
      requestAnimationFrame(animate)
    } else {
      displayStreak.value = result
      showBurst.value = true
      setTimeout(() => {
        phase.value = 'done'
        appStore.refreshTodayData()
      }, 300)
    }
  }

  requestAnimationFrame(animate)
}

// 获取打卡等级
function getLevel(total: number): { title: string; emoji: string } {
  if (total >= 365) return { title: '年度达人', emoji: '👑' }
  if (total >= 180) return { title: '半年之星', emoji: '🌟' }
  if (total >= 90) return { title: '季度精英', emoji: '💎' }
  if (total >= 60) return { title: '两月勇士', emoji: '🏅' }
  if (total >= 30) return { title: '月度先锋', emoji: '🥇' }
  if (total >= 14) return { title: '两周达人', emoji: '🥈' }
  if (total >= 7) return { title: '一周坚持', emoji: '🥉' }
  if (total >= 3) return { title: '起步新秀', emoji: '🌱' }
  return { title: '初始阶段', emoji: '🎯' }
}

// 最近打卡记录
const recentRecords = computed(() => {
  const records = checkinData.value.records
  return records.slice(-14).reverse()
})

// 格式化日期
function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}

function formatWeekday(dateStr: string): string {
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  const d = new Date(dateStr)
  return `周${weekdays[d.getDay()]}`
}

// 打卡热力图数据（最近 26 周）
const checkinHeatmapData = computed(() => {
  const data: Record<string, number> = {}
  const records = checkinData.value.records
  for (const record of records) {
    data[record.date] = 100 // 打卡 = 100%
  }
  return data
})

// 热力图点击
function onHeatmapClick(dateStr: string) {
  router.push(`/day/${dateStr}`)
}

// 连续天数可视化（最近7天）
const last7Days = computed(() => {
  const days = []
  const today = new Date()
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const dateStr = `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
    const hasCheckin = checkinData.value.records.some(r => r.date === dateStr)
    const isToday = i === 0
    const weekday = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
    days.push({ dateStr, hasCheckin, isToday, weekday, label: d.getDate().toString() })
  }
  return days
})
</script>

<template>
  <div class="checkin-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="16" />
        <span>返回</span>
      </button>
      <h1>打卡</h1>
    </header>

    <main class="main-content">
      <!-- 打卡状态区 -->
      <section class="status-section">
        <!-- 未打卡状态 -->
        <template v-if="!hasCheckedInToday && phase === 'idle'">
          <div class="status-card">
            <div class="status-icon" v-if="canCheckinToday">🎯</div>
            <div class="status-icon waiting" v-else>⏳</div>
            <h2 class="status-title" v-if="canCheckinToday">今日计划已完成！</h2>
            <h2 class="status-title" v-else>今日计划尚未完成</h2>
            <p class="status-desc" v-if="canCheckinToday">
              「{{ planName }}」计划已100%达成，快来打卡吧
            </p>
            <p class="status-desc" v-else>
              完成今天的计划后，可以回来打卡
            </p>
            <button
              v-if="canCheckinToday"
              class="checkin-btn"
              @click="doCheckin"
            >
              <span class="btn-icon">👆</span>
              <span>点击打卡</span>
            </button>
            <button
              v-else
              class="checkin-btn disabled"
              disabled
            >
              <span>完成计划后可打卡</span>
            </button>
          </div>
        </template>

        <!-- 打卡动画中 -->
        <template v-else-if="phase === 'animating'">
          <div class="status-card animating">
            <div class="anim-streak">
              <Flame :size="48" class="big-flame" />
              <div class="anim-number">{{ displayStreak }}</div>
              <div class="anim-unit">天</div>
            </div>
            <p class="anim-desc">打卡中...</p>
            <!-- 粒子爆发 -->
            <div v-if="showBurst" class="burst-particles">
              <span v-for="i in 12" :key="i" class="particle" :style="{ '--i': i }"></span>
            </div>
          </div>
        </template>

        <!-- 已打卡/打卡完成 -->
        <template v-else>
          <div class="status-card checked">
            <div class="checked-icon">
              <div class="check-circle">
                <Check :size="32" />
              </div>
            </div>
            <h2 class="checked-title">今日已打卡</h2>
            <div class="checked-streak">
              <Flame :size="20" class="flame-sm" />
              <span>连续 <strong>{{ phase === 'done' ? displayStreak : currentStreak }}</strong> 天</span>
            </div>
            <p class="checked-desc" v-if="phase === 'done'">太棒了！继续保持！</p>
            <div v-if="showBurst" class="burst-particles">
              <span v-for="i in 12" :key="i" class="particle" :style="{ '--i': i }"></span>
            </div>
          </div>
        </template>
      </section>

      <!-- 统计数据 -->
      <section class="stats-grid">
        <div class="stat-card">
          <Flame :size="24" class="stat-icon streak" />
          <div class="stat-info">
            <span class="stat-value">{{ currentStreak }}</span>
            <span class="stat-label">连续打卡</span>
          </div>
        </div>
        <div class="stat-card">
          <Trophy :size="24" class="stat-icon record" />
          <div class="stat-info">
            <span class="stat-value">{{ longestStreak }}</span>
            <span class="stat-label">最长连续</span>
          </div>
        </div>
        <div class="stat-card">
          <Calendar :size="24" class="stat-icon total" />
          <div class="stat-info">
            <span class="stat-value">{{ totalCheckins }}</span>
            <span class="stat-label">累计打卡</span>
          </div>
        </div>
        <div class="stat-card">
          <TrendingUp :size="24" class="stat-icon level" />
          <div class="stat-info">
            <span class="stat-value level-value">
              {{ getLevel(totalCheckins).emoji }} {{ getLevel(totalCheckins).title }}
            </span>
            <span class="stat-label">当前等级</span>
          </div>
        </div>
      </section>

      <!-- 最近7天连续可视化 -->
      <section class="week-visualizer">
        <h3 class="section-title">最近 7 天</h3>
        <div class="week-dots">
          <div
            v-for="day in last7Days"
            :key="day.dateStr"
            class="week-dot-item"
            :class="{ 'is-today': day.isToday, 'has-checkin': day.hasCheckin }"
          >
            <div class="week-dot">
              <Flame v-if="day.hasCheckin" :size="12" />
            </div>
            <span class="week-label">{{ day.weekday }}</span>
          </div>
        </div>
      </section>

      <!-- 打卡热力图 -->
      <section class="heatmap-section">
        <div class="section-header-row">
          <div class="section-title-row">
            <BarChart3 :size="16" class="section-icon" />
            <h3 class="section-title">打卡日历</h3>
          </div>
        </div>
        <ContributionHeatmap
          :data="checkinHeatmapData"
          :weeks="26"
          color-mode="checkin"
          title=""
          @cell-click="onHeatmapClick"
        />
      </section>

      <!-- 最近打卡记录 -->
      <section class="history-section">
        <h3 class="section-title">打卡历史</h3>
        <div class="history-list" v-if="recentRecords.length > 0">
          <div
            v-for="record in recentRecords"
            :key="record.date"
            class="history-item"
          >
            <div class="history-date">
              <span class="date-text">{{ formatDate(record.date) }}</span>
              <span class="date-weekday">{{ formatWeekday(record.date) }}</span>
            </div>
            <div class="history-info">
              <span class="history-plan">{{ record.planName }}</span>
              <span class="history-progress" v-if="record.progress >= 100">100%</span>
            </div>
            <Flame :size="14" class="history-flame" />
          </div>
        </div>
        <div class="empty-state" v-else>
          <p>暂无打卡记录</p>
          <p class="hint">完成今天的计划后来打卡吧</p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.checkin-view {
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

.back-btn {
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

.back-btn:hover { background: var(--color-bg-tertiary); }

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

/* 打卡状态卡片 */
.status-card {
  background: linear-gradient(145deg, var(--color-bg-secondary) 0%, var(--color-bg-tertiary) 100%);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl) var(--spacing-lg);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  position: relative;
  overflow: hidden;
}

.status-card.checked {
  background: linear-gradient(145deg, rgba(34, 197, 94, 0.05) 0%, rgba(34, 197, 94, 0.1) 100%);
  border-color: rgba(34, 197, 94, 0.3);
}

.status-icon {
  font-size: 3rem;
  animation: bounce 2s ease-in-out infinite;
}

.status-icon.waiting {
  animation: none;
  opacity: 0.5;
}

.status-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-hover) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.status-desc {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* 打卡按钮 */
.checkin-btn {
  margin-top: var(--spacing-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: 14px 48px;
  background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
  border: none;
  border-radius: 32px;
  color: #1a1a2e;
  font-size: 1.125rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 20px rgba(255, 215, 0, 0.4);
}

.checkin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(255, 215, 0, 0.6);
}

.checkin-btn:active {
  transform: translateY(0);
}

.checkin-btn.disabled {
  background: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
  box-shadow: none;
  cursor: not-allowed;
  font-size: 0.875rem;
}

.btn-icon {
  font-size: 1.25rem;
}

/* 已打卡状态 */
.checked-icon {
  margin-bottom: var(--spacing-sm);
}

.check-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 20px rgba(34, 197, 94, 0.3);
}

.checked-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-success);
  margin: 0;
}

.checked-streak {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.1), rgba(255, 215, 0, 0.1));
  border: 1px solid rgba(255, 215, 0, 0.2);
  border-radius: var(--radius-full);
  font-size: 0.9375rem;
}

.checked-streak strong {
  color: #ff8c00;
  font-weight: 700;
  font-size: 1.125rem;
  font-family: var(--font-mono);
}

.flame-sm {
  color: #ff8c00;
}

.checked-desc {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* 动画 */
.anim-streak {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.big-flame {
  color: #ff8c00;
  filter: drop-shadow(0 0 20px rgba(255, 140, 0, 0.8));
  animation: flameFlicker 1.5s ease-in-out infinite;
}

.anim-number {
  font-size: 5rem;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-family: var(--font-mono);
}

.anim-unit {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  letter-spacing: 4px;
}

.anim-desc {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* 粒子爆发 */
.burst-particles {
  position: absolute;
  top: 50%;
  left: 50%;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #ffd700;
  border-radius: 50%;
  animation: particleBurst 0.8s ease-out forwards;
  transform: translate(-50%, -50%);
}

.particle:nth-child(even) { background: #ff8c00; }
.particle:nth-child(3n) { background: #ffed4e; width: 6px; height: 6px; }

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes flameFlicker {
  0%, 100% { transform: scale(1) rotate(-2deg); }
  50% { transform: scale(1.05) rotate(2deg); }
}

@keyframes particleBurst {
  0% {
    transform: translate(-50%, -50%) translate(0, 0) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%)
      translate(calc(cos(var(--i) * 30deg) * 100px), calc(sin(var(--i) * 30deg) * 100px))
      scale(0);
    opacity: 0;
  }
}

/* 统计网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.stat-icon {
  flex-shrink: 0;
}

.stat-icon.streak { color: #ff8c00; }
.stat-icon.record { color: #ffd700; }
.stat-icon.total { color: var(--color-primary); }
.stat-icon.level { color: var(--color-success); }

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-text-primary);
  line-height: 1.2;
}

.stat-value.level-value {
  font-size: 0.9375rem;
  font-family: var(--font-sans);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* 最近7天可视化 */
.section-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

.week-visualizer {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.week-dots {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: var(--spacing-sm);
}

.week-dot-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.week-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  color: #ff8c00;
}

.week-dot-item.has-checkin .week-dot {
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.2), rgba(255, 215, 0, 0.2));
  border-color: rgba(255, 140, 0, 0.5);
}

.week-dot-item.is-today .week-dot {
  border-color: var(--color-primary);
  border-width: 2px;
}

.week-label {
  font-size: 0.6875rem;
  color: var(--color-text-tertiary);
}

.week-dot-item.is-today .week-label {
  color: var(--color-primary);
  font-weight: 600;
}

/* 打卡历史 */
.history-section {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.history-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.history-date {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}

.date-text {
  font-size: 0.875rem;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--color-text-primary);
}

.date-weekday {
  font-size: 0.6875rem;
  color: var(--color-text-tertiary);
}

.history-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-plan {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.history-progress {
  font-size: 0.75rem;
  color: var(--color-success);
  font-family: var(--font-mono);
}

.history-flame {
  color: #ff8c00;
  flex-shrink: 0;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-tertiary);
}

.empty-state .hint {
  font-size: 0.8125rem;
  margin-top: var(--spacing-xs);
}

/* 热力图区域 */
.heatmap-section {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-icon {
  color: #ff8c00;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin: 0;
}
</style>
