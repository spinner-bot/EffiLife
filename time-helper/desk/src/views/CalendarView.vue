<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Flame, Check } from 'lucide-vue-next'
import { DataService } from '@/services/dataService'
import { CheckinSystem } from '@/data'

const router = useRouter()

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const showQuickNav = ref(false)

// 每月数据缓存
interface DayMeta {
  dateStr: string
  date: number
  hasCheckin: boolean      // 是否打卡
  progress: number         // 完成度 0-100
  hasRecords: boolean      // 是否有记录
  planName: string         // 当天计划名
}

const monthData = ref<Record<string, DayMeta>>({})
const isLoading = ref(false)

// 获取某天的元数据
async function fetchDayMeta(dateStr: string): Promise<DayMeta> {
  const checkinData = CheckinSystem.getData()
  const hasCheckin = checkinData.records.some(r => r.date === dateStr)
  const stat = await DataService.calcRealTimeStat(dateStr)
  return {
    dateStr,
    date: new Date(dateStr).getDate(),
    hasCheckin,
    progress: stat.progress,
    hasRecords: stat.has_records,
    planName: stat.plan_name
  }
}

// 加载整月数据
async function loadMonthData() {
  isLoading.value = true
  const year = currentYear.value
  const month = currentMonth.value
  const lastDay = new Date(year, month, 0).getDate()

  const newData: Record<string, DayMeta> = {}

  // 并行获取
  const promises = []
  for (let d = 1; d <= lastDay; d++) {
    const dateStr = `${year}-${month.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`
    promises.push(
      fetchDayMeta(dateStr).then(meta => { newData[dateStr] = meta })
    )
  }
  await Promise.all(promises)
  monthData.value = newData
  isLoading.value = false
}

// 获取月份日历网格
const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value

  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const daysInMonth = lastDay.getDate()
  const startWeekday = firstDay.getDay() || 7 // 1-7, 周一为1

  const days: (DayMeta | null)[] = []

  // 填充前面的空白
  for (let i = 1; i < startWeekday; i++) {
    days.push(null)
  }

  // 填充日期
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${month.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`
    days.push(monthData.value[dateStr] || {
      dateStr,
      date: d,
      hasCheckin: false,
      progress: 0,
      hasRecords: false,
      planName: ''
    })
  }

  return days
})

// 月度统计
const monthStats = computed(() => {
  const allDays = Object.values(monthData.value)
  const daysWithRecords = allDays.filter(d => d.hasRecords).length
  const daysWithCheckin = allDays.filter(d => d.hasCheckin).length
  const avgProgress = allDays.length > 0
    ? Math.round(allDays.filter(d => d.hasRecords).reduce((sum, d) => sum + d.progress, 0) / Math.max(1, daysWithRecords))
    : 0
  return { daysWithRecords, daysWithCheckin, avgProgress }
})

// 导航
function prevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function prevYear() {
  currentYear.value--
}

function nextYear() {
  currentYear.value++
}

function goToday() {
  const today = new Date()
  currentYear.value = today.getFullYear()
  currentMonth.value = today.getMonth() + 1
}

function isCurrentMonth() {
  const today = new Date()
  return currentYear.value === today.getFullYear() && currentMonth.value === today.getMonth() + 1
}

function isToday(dateStr: string): boolean {
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`
  return dateStr === todayStr
}

function isFuture(dateStr: string): boolean {
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`
  return dateStr > todayStr
}

// 进度条颜色
function getProgressBg(progress: number, hasRecords: boolean): string {
  if (!hasRecords) return 'transparent'
  if (progress >= 100) return 'rgba(34, 197, 94, 0.15)'
  if (progress >= 70) return 'rgba(234, 179, 8, 0.12)'
  if (progress >= 40) return 'rgba(245, 158, 11, 0.12)'
  if (progress > 0) return 'rgba(239, 68, 68, 0.08)'
  return 'transparent'
}

function getProgressBorderColor(progress: number, hasRecords: boolean): string {
  if (!hasRecords) return 'var(--color-border)'
  if (progress >= 100) return 'rgba(34, 197, 94, 0.5)'
  if (progress >= 70) return 'rgba(234, 179, 8, 0.4)'
  if (progress >= 40) return 'rgba(245, 158, 11, 0.3)'
  if (progress > 0) return 'rgba(239, 68, 68, 0.25)'
  return 'var(--color-border)'
}

// 点击日期
function onDayClick(day: DayMeta) {
  if (isFuture(day.dateStr)) return
  router.push(`/day/${day.dateStr}`)
}

// 星期标题
const weekDays = ['一', '二', '三', '四', '五', '六', '日']

// 监听月份变化，重新加载数据
watch([currentYear, currentMonth], loadMonthData)

onMounted(loadMonthData)
</script>

<template>
  <div class="calendar-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="16" />
        <span>返回</span>
      </button>
      <h1>日历</h1>
    </header>

    <main class="main-content">
      <!-- 月度概览卡片 -->
      <div class="month-overview" v-if="monthStats.daysWithRecords > 0">
        <div class="overview-stat">
          <span class="overview-value">{{ monthStats.daysWithRecords }}</span>
          <span class="overview-label">有记录</span>
        </div>
        <div class="overview-stat">
          <span class="overview-value checkin-color">{{ monthStats.daysWithCheckin }}</span>
          <span class="overview-label">已打卡</span>
        </div>
        <div class="overview-stat">
          <span class="overview-value">{{ monthStats.avgProgress }}%</span>
          <span class="overview-label">平均完成</span>
        </div>
      </div>

      <!-- 导航栏 -->
      <div class="nav-bar">
        <button v-if="showQuickNav" class="nav-btn" @click="prevYear" title="上一年">
          <ChevronsLeft :size="16" />
        </button>
        <button class="nav-btn" @click="prevMonth" title="上个月">
          <ChevronLeft :size="16" />
        </button>
        <div class="current-month">{{ currentYear }}年{{ currentMonth }}月</div>
        <button
          v-if="!isCurrentMonth()"
          class="today-btn"
          @click="goToday"
        >
          返回今天
        </button>
        <button class="nav-btn" @click="nextMonth" title="下个月">
          <ChevronRight :size="16" />
        </button>
        <button v-if="showQuickNav" class="nav-btn" @click="nextYear" title="下一年">
          <ChevronsRight :size="16" />
        </button>
      </div>

      <!-- 加载指示 -->
      <div v-if="isLoading" class="loading-bar">
        <div class="loading-fill"></div>
      </div>

      <!-- 星期标题 -->
      <div class="week-header">
        <div v-for="day in weekDays" :key="day" class="week-day">{{ day }}</div>
      </div>

      <!-- 日历网格 -->
      <div class="calendar-grid">
        <template v-for="(day, index) in calendarDays" :key="index">
          <div
            v-if="day"
            class="day-cell"
            :class="{
              today: isToday(day.dateStr),
              'has-records': day.hasRecords,
              'has-checkin': day.hasCheckin,
              'is-future': isFuture(day.dateStr),
              'perfect': day.progress >= 100 && day.hasRecords
            }"
            :style="{
              backgroundColor: getProgressBg(day.progress, day.hasRecords),
              borderColor: getProgressBorderColor(day.progress, day.hasRecords)
            }"
            @click="onDayClick(day)"
          >
            <div class="day-number">{{ day.date }}</div>
            <!-- 完成度小条 -->
            <div class="day-progress-bar" v-if="day.hasRecords">
              <div
                class="day-progress-fill"
                :style="{ width: Math.min(100, day.progress) + '%' }"
              ></div>
            </div>
            <!-- 打卡标记 -->
            <div class="day-checkin-mark" v-if="day.hasCheckin" title="已打卡">
              <Flame :size="10" />
            </div>
          </div>
          <div v-else class="day-cell empty"></div>
        </template>
      </div>

      <!-- 图例 -->
      <div class="legend">
        <div class="legend-item">
          <div class="legend-dot" style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.5)"></div>
          <span>100%</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background: rgba(234, 179, 8, 0.12); border: 1px solid rgba(234, 179, 8, 0.4)"></div>
          <span>70%+</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3)"></div>
          <span>40%+</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25)"></div>
          <span>&lt;40%</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot legend-checkin">
            <Flame :size="8" />
          </div>
          <span>已打卡</span>
        </div>
      </div>

      <!-- 快速翻页选项 -->
      <div class="options">
        <label class="checkbox-label">
          <input type="checkbox" v-model="showQuickNav" />
          <span>快速翻页</span>
        </label>
      </div>
    </main>
  </div>
</template>

<style scoped>
.calendar-view {
  min-height: 100vh;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
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

.back-btn:hover {
  background: var(--color-bg-tertiary);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

/* 月度概览 */
.month-overview {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.overview-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.overview-value {
  font-size: 1.5rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-text-primary);
}

.overview-value.checkin-color {
  color: #ff8c00;
}

.overview-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* 导航栏 */
.nav-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.current-month {
  flex: 1;
  text-align: center;
  font-size: 1.25rem;
  font-weight: 600;
}

.today-btn {
  padding: var(--spacing-xs) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.today-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

/* 加载指示条 */
.loading-bar {
  height: 2px;
  background: var(--color-bg-tertiary);
  border-radius: 1px;
  margin-bottom: var(--spacing-sm);
  overflow: hidden;
}

.loading-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 1px;
  animation: loadingSlide 1.2s ease-in-out infinite;
  width: 30%;
}

@keyframes loadingSlide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}

/* 星期标题 */
.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  margin-bottom: 6px;
}

.week-day {
  text-align: center;
  padding: var(--spacing-sm);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 日历网格 */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.day-cell {
  position: relative;
  aspect-ratio: 1;
  background: var(--color-bg-secondary);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.day-cell:hover:not(.empty):not(.is-future) {
  transform: scale(1.05);
  box-shadow: var(--shadow-md);
  z-index: 1;
}

.day-cell.today {
  border-color: var(--color-primary);
  border-width: 2px;
}

.day-cell.is-future {
  opacity: 0.4;
  cursor: default;
}

.day-cell.empty {
  background: transparent;
  border-color: transparent;
  cursor: default;
}

.day-cell.empty:hover {
  transform: none;
  box-shadow: none;
}

.day-cell.perfect {
  border-color: rgba(34, 197, 94, 0.6);
}

.day-number {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1;
}

.day-cell.is-future .day-number {
  color: var(--color-text-tertiary);
}

/* 日进度小条 */
.day-progress-bar {
  width: 100%;
  height: 3px;
  background: var(--color-bg-tertiary);
  border-radius: 1.5px;
  overflow: hidden;
  margin-top: auto;
}

.day-progress-fill {
  height: 100%;
  border-radius: 1.5px;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.day-cell.perfect .day-progress-fill {
  background: var(--color-success);
}

/* 打卡标记 */
.day-checkin-mark {
  position: absolute;
  top: 3px;
  right: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  background: rgba(255, 140, 0, 0.2);
  border-radius: 50%;
  color: #ff8c00;
}

/* 图例 */
.legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding: var(--spacing-sm);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-checkin {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 140, 0, 0.2);
  color: #ff8c00;
  border-radius: 50%;
}

.options {
  margin-top: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.checkbox-label input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}
</style>
