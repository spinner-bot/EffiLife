<script setup lang="ts">
import { computed } from 'vue'

/**
 * GitHub 风格贡献热力图
 * 可复用于日历视图和打卡视图
 */

interface HeatmapCell {
  date: string
  value: number       // 0-4 级别
  label: string
  isFuture: boolean
  isToday: boolean
}

const props = withDefaults(defineProps<{
  /** 数据：date -> value (0-100 或任意数值) */
  data: Record<string, number>
  /** 显示多少周（默认 26 周 ≈ 6 个月） */
  weeks?: number
  /** 颜色模式 */
  colorMode?: 'progress' | 'checkin' | 'hours'
  /** 单元格尺寸 */
  cellSize?: number
  /** 单元格间距 */
  cellGap?: number
  /** 标题 */
  title?: string
}>(), {
  weeks: 26,
  colorMode: 'progress',
  cellSize: 13,
  cellGap: 3,
  title: ''
})

// 计算热力图单元格
const cells = computed(() => {
  const totalDays = props.weeks * 7
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // 计算起始日期（从今天往前推 totalDays 天，对齐到周日）
  const endDate = new Date(today)
  const startDate = new Date(today)
  startDate.setDate(startDate.getDate() - totalDays + 1)
  // 对齐到周日
  const startDay = startDate.getDay()
  startDate.setDate(startDate.getDate() - startDay)

  const result: HeatmapCell[] = []
  const current = new Date(startDate)

  while (current <= endDate) {
    const dateStr = formatDate(current)
    const value = props.data[dateStr] || 0
    const isFuture = current > today
    const isToday = current.getTime() === today.getTime()

    let level: number
    if (value === 0) level = 0
    else if (value < 25) level = 1
    else if (value < 50) level = 2
    else if (value < 75) level = 3
    else level = 4

    result.push({
      date: dateStr,
      value: level,
      label: `${dateStr}: ${Math.round(value)}${props.colorMode === 'hours' ? 'h' : '%'}`,
      isFuture,
      isToday
    })

    current.setDate(current.getDate() + 1)
  }

  return result
})

// 按周分组
const weeks = computed(() => {
  const result: HeatmapCell[][] = []
  let currentWeek: HeatmapCell[] = []

  for (const cell of cells.value) {
    currentWeek.push(cell)
    if (currentWeek.length === 7) {
      result.push(currentWeek)
      currentWeek = []
    }
  }
  if (currentWeek.length > 0) {
    result.push(currentWeek)
  }

  return result
})

// 月份标签
const monthLabels = computed(() => {
  const labels: { text: string; weekIndex: number }[] = []
  const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  let lastMonth = -1

  for (let i = 0; i < weeks.value.length; i++) {
    const firstDay = weeks.value[i][0]
    const d = new Date(firstDay.date)
    const month = d.getMonth()
    if (month !== lastMonth) {
      labels.push({ text: monthNames[month], weekIndex: i })
      lastMonth = month
    }
  }

  return labels
})

// 颜色映射
function getCellColor(cell: HeatmapCell): string {
  if (cell.isFuture) return 'transparent'

  const colors = {
    progress: [
      'var(--color-bg-tertiary)',
      'rgba(34, 197, 94, 0.25)',
      'rgba(34, 197, 94, 0.45)',
      'rgba(34, 197, 94, 0.65)',
      'rgba(34, 197, 94, 0.9)'
    ],
    checkin: [
      'var(--color-bg-tertiary)',
      'rgba(255, 140, 0, 0.25)',
      'rgba(255, 140, 0, 0.45)',
      'rgba(255, 140, 0, 0.65)',
      'rgba(255, 140, 0, 0.9)'
    ],
    hours: [
      'var(--color-bg-tertiary)',
      'rgba(99, 102, 241, 0.25)',
      'rgba(99, 102, 241, 0.45)',
      'rgba(99, 102, 241, 0.65)',
      'rgba(99, 102, 241, 0.9)'
    ]
  }

  return colors[props.colorMode][cell.value]
}

function getCellBorder(cell: HeatmapCell): string {
  if (cell.isToday) {
    return '1.5px solid var(--color-primary)'
  }
  return 'none'
}

// 统计
const stats = computed(() => {
  const nonEmpty = cells.value.filter(c => !c.isFuture && c.value > 0)
  const total = nonEmpty.length
  const maxVal = Math.max(...cells.value.filter(c => !c.isFuture).map(c => c.value), 0)

  // 计算连续天数
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  let currentStreak = 0
  let longestStreak = 0
  let tempStreak = 0
  const sortedNonFuture = cells.value.filter(c => !c.isFuture).reverse()

  for (const cell of sortedNonFuture) {
    if (cell.value > 0) {
      tempStreak++
      longestStreak = Math.max(longestStreak, tempStreak)
      if (currentStreak === tempStreak - 1 || currentStreak === tempStreak) {
        currentStreak = tempStreak
      }
    } else {
      if (tempStreak === currentStreak && sortedNonFuture.indexOf(cell) > 0) {
        // 今天的格子如果为空，不算断
        const d = new Date(cell.date)
        if (d.getTime() !== today.getTime()) {
          currentStreak = 0
        }
      }
      tempStreak = 0
    }
  }

  return { total, maxVal, currentStreak, longestStreak }
})

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}

// 图例
const legendLevels = [0, 1, 2, 3, 4]
const legendLabels = ['0', '25%', '50%', '75%', '100%']

// 计算 SVG 尺寸
const svgWidth = computed(() => weeks.value.length * (props.cellSize + props.cellGap) + props.cellGap)
const svgHeight = computed(() => 7 * (props.cellSize + props.cellGap) + props.cellGap + 20) // +20 for month labels

defineEmits<{
  (e: 'cell-click', date: string): void
}>()
</script>

<template>
  <div class="contribution-heatmap">
    <div class="heatmap-header" v-if="title">
      <h3 class="heatmap-title">{{ title }}</h3>
      <div class="heatmap-stats">
        <span class="heatmap-stat">活跃 <strong>{{ stats.total }}</strong> 天</span>
      </div>
    </div>

    <div class="heatmap-container">
      <!-- 月份标签 -->
      <div class="month-labels">
        <span
          v-for="(label, i) in monthLabels"
          :key="i"
          class="month-label"
          :style="{ left: `${label.weekIndex * (cellSize + cellGap) + cellGap}px` }"
        >{{ label.text }}</span>
      </div>

      <!-- 星期标签 -->
      <div class="weekday-labels">
        <span
          v-for="(day, i) in weekDays"
          :key="i"
          class="weekday-label"
          :style="{ top: `${i * (cellSize + cellGap) + cellGap + 18}px` }"
        >{{ i % 2 === 1 ? day : '' }}</span>
      </div>

      <!-- 热力图网格 -->
      <svg
        :width="svgWidth + 24"
        :height="svgHeight"
        class="heatmap-svg"
      >
        <g transform="translate(24, 18)">
          <g v-for="(week, wi) in weeks" :key="wi">
            <rect
              v-for="(cell, di) in week"
              :key="`${wi}-${di}`"
              :x="wi * (cellSize + cellGap)"
              :y="di * (cellSize + cellGap)"
              :width="cellSize"
              :height="cellSize"
              :rx="2"
              :ry="2"
              :fill="getCellColor(cell)"
              :style="{ stroke: cell.isToday ? 'var(--color-primary)' : 'none', strokeWidth: cell.isToday ? 1.5 : 0, cursor: cell.isFuture ? 'default' : 'pointer' }"
              @click="!cell.isFuture && $emit('cell-click', cell.date)"
            >
              <title>{{ cell.label }}</title>
            </rect>
          </g>
        </g>
      </svg>
    </div>

    <!-- 图例 -->
    <div class="heatmap-legend">
      <span class="legend-label">少</span>
      <div
        v-for="(level, i) in legendLevels"
        :key="level"
        class="legend-cell"
        :style="{
          width: cellSize + 'px',
          height: cellSize + 'px',
          backgroundColor: getCellColor({ date: '', value: level, label: '', isFuture: false, isToday: false })
        }"
      ></div>
      <span class="legend-label">多</span>
    </div>
  </div>
</template>

<style scoped>
.contribution-heatmap {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.heatmap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.heatmap-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin: 0;
}

.heatmap-stats {
  display: flex;
  gap: var(--spacing-md);
}

.heatmap-stat {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.heatmap-stat strong {
  color: var(--color-text-primary);
  font-weight: 600;
  font-family: var(--font-mono);
}

.heatmap-container {
  position: relative;
  overflow-x: auto;
  padding-top: 4px;
}

.month-labels {
  position: relative;
  height: 16px;
  margin-left: 24px;
  margin-bottom: 2px;
}

.month-label {
  position: absolute;
  font-size: 0.625rem;
  color: var(--color-text-tertiary);
  line-height: 1;
}

.weekday-labels {
  position: absolute;
  left: 0;
  top: 18px;
  display: flex;
  flex-direction: column;
  width: 20px;
}

.weekday-label {
  position: absolute;
  font-size: 0.5625rem;
  color: var(--color-text-tertiary);
  line-height: 1;
  text-align: right;
  width: 18px;
}

.heatmap-svg {
  display: block;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 3px;
  justify-content: flex-end;
  margin-top: var(--spacing-xs);
}

.legend-label {
  font-size: 0.625rem;
  color: var(--color-text-tertiary);
  margin: 0 4px;
}

.legend-cell {
  border-radius: 2px;
}
</style>
