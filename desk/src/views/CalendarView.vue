<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { DataService, rgbToHex, hoursToHm } from '@/services/dataService'
import { ArrowLeft, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-vue-next'

const router = useRouter()
const appStore = useAppStore()

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const showQuickNav = ref(false)

const plans = computed(() => appStore.plans)

// 获取月份日历数据
const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value

  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const daysInMonth = lastDay.getDate()
  const startWeekday = firstDay.getDay() || 7 // 1-7, 周一为1

  const days: Array<{ date: number; dateStr: string; isCurrentMonth: boolean } | null> = []

  // 填充前面的空白
  for (let i = 1; i < startWeekday; i++) {
    days.push(null)
  }

  // 填充日期
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${month.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`
    days.push({ date: d, dateStr, isCurrentMonth: true })
  }

  return days
})

// 获取某天的统计数据
async function getDayStat(dateStr: string) {
  return await DataService.calcRealTimeStat(dateStr)
}

// 获取某天的颜色
function getDayColor(dateStr: string): string {
  // 这里需要异步获取，先用默认颜色
  const dayPlan = DataService.getDayPlan(dateStr)
  return dayPlan.then(plan => {
    const p = plans.value[plan.name]
    if (p && p.color) {
      const k = appStore.config.whiten_k
      const r = Math.floor(p.color[0] * (1 - k) + 255 * k)
      const g = Math.floor(p.color[1] * (1 - k) + 255 * k)
      const b = Math.floor(p.color[2] * (1 - k) + 255 * k)
      return rgbToHex(r, g, b)
    }
    return '#e4e4e7'
  })
}

// 完成度颜色
function getProgressColor(progress: number): string {
  if (progress === 0) return 'var(--color-text-primary)'
  if (progress < 40) return 'var(--color-progress-low)'
  if (progress < 70) return 'var(--color-progress-medium)'
  if (progress < 90) return 'var(--color-progress-good)'
  return 'var(--color-progress-high)'
}

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

// 点击日期
function onDayClick(dateStr: string) {
  router.push(`/day/${dateStr}`)
}

// 星期标题
const weekDays = ['一', '二', '三', '四', '五', '六', '日']
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

      <!-- 星期标题 -->
      <div class="week-header">
        <div v-for="day in weekDays" :key="day" class="week-day">{{ day }}</div>
      </div>

      <!-- 日历网格 -->
      <div class="calendar-grid">
        <template v-for="(day, index) in calendarDays" :key="index">
          <div v-if="day" class="day-cell" :class="{ today: isToday(day.dateStr) }" @click="onDayClick(day.dateStr)">
            <div class="day-number">{{ day.date }}日</div>
            <div class="day-progress" :data-date="day.dateStr">
              <span class="loading">...</span>
            </div>
          </div>
          <div v-else class="day-cell empty"></div>
        </template>
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

.nav-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
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

.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 4px;
}

.week-day {
  text-align: center;
  padding: var(--spacing-sm);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day-cell {
  aspect-ratio: 1;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.day-cell:hover {
  border-color: var(--color-border-hover);
  transform: scale(1.02);
}

.day-cell.today {
  border-color: var(--color-primary);
  border-width: 2px;
}

.day-cell.empty {
  background: transparent;
  border-color: transparent;
  cursor: default;
}

.day-cell.empty:hover {
  transform: none;
}

.day-number {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.day-progress {
  font-size: 0.75rem;
  font-weight: 600;
}

.day-progress .loading {
  color: var(--color-text-tertiary);
}

.options {
  margin-top: var(--spacing-lg);
  display: flex;
  align-items: center;
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
