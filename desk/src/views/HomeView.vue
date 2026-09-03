<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { hoursToHm } from '@/services/dataService'
import { FileText, Calendar, FolderKanban, Settings } from 'lucide-vue-next'

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
    </header>

    <main class="main-content">
      <section class="clock-section">
        <div class="time-display">{{ currentTime }}</div>
        <div class="date-display">{{ currentDate }}</div>
      </section>

      <section class="stats-section">
        <div class="stats-card" @click="router.push('/records')">
          <h2 class="stats-title">今日时间统计</h2>
          <div class="stats-content" v-if="stat && stat.plan_exists">
            <div
              v-for="(target, tag) in stat.target"
              :key="tag"
              class="stat-item"
              :class="{ 'is-bg-tag': tag === stat.bg_tag, 'is-exceeded': (stat.raw_stat[tag] || 0) > target }"
            >
              <span class="stat-prefix">{{ tag === stat.bg_tag ? '🟢 背景类别' : '🔹' }}</span>
              <span class="stat-name">{{ tag }}</span>
              <span class="stat-value">
                {{ hoursToHm(stat.stat[tag] || 0) }} / {{ hoursToHm(target) }}
              </span>
              <span class="stat-percent">({{ Math.round((stat.raw_stat[tag] || 0) / target * 100) }}%)</span>
              <span v-if="(stat.raw_stat[tag] || 0) > target" class="stat-exceed">
                超出{{ hoursToHm((stat.raw_stat[tag] || 0) - target) }}
              </span>
            </div>
            <div class="progress-row">
              <span class="progress-label">📊 有效总完成度：</span>
              <span class="progress-value" :style="{ color: getProgressColor(stat.progress) }">
                {{ stat.progress }}%
              </span>
              <span class="progress-total">（总计目标：{{ hoursToHm(Object.values(stat.target).reduce((a, b) => a + b, 0)) }}）</span>
            </div>
          </div>
          <div class="stats-content" v-else>
            <p class="empty-hint">暂无计划数据，点击前往管理</p>
          </div>
        </div>
      </section>

      <nav class="nav-buttons">
        <button class="nav-btn" @click="router.push('/records')">
          <FileText :size="24" />
          <span>记录</span>
        </button>
        <button class="nav-btn" @click="router.push('/calendar')">
          <Calendar :size="24" />
          <span>日历</span>
        </button>
        <button class="nav-btn" @click="router.push('/management')">
          <FolderKanban :size="24" />
          <span>管理</span>
        </button>
        <button class="nav-btn" @click="router.push('/settings')">
          <Settings :size="24" />
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
  text-align: center;
  padding: var(--spacing-md) 0;
}

.logo {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
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

.stats-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.stats-content {
  padding: var(--spacing-sm) 0;
}

.stat-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) 0;
  font-size: 0.875rem;
  color: var(--color-text-primary);
}

.stat-item.is-exceeded {
  color: var(--color-error);
}

.stat-prefix {
  font-size: 0.75rem;
}

.stat-name {
  font-weight: 500;
}

.stat-value {
  color: var(--color-text-secondary);
}

.stat-percent {
  color: var(--color-text-tertiary);
}

.stat-exceed {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--color-error);
}

.progress-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  font-size: 0.875rem;
}

.progress-label {
  font-weight: 600;
}

.progress-value {
  font-weight: 700;
  font-size: 1rem;
}

.progress-total {
  color: var(--color-text-tertiary);
}

.empty-hint {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  padding: var(--spacing-lg) 0;
}

.nav-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
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

.footer {
  text-align: center;
  padding: var(--spacing-md) 0;
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
}
</style>
