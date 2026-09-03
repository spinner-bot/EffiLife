<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentTime = ref('')
const currentDate = ref('')
let timer: number | null = null

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
  currentDate.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
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
        <div class="stats-card">
          <h2 class="stats-title">今日时间统计</h2>
          <div class="stats-content">
            <p class="empty-hint">暂无数据，点击下方按钮开始记录</p>
          </div>
        </div>
      </section>

      <nav class="nav-buttons">
        <button class="nav-btn" @click="router.push('/records')">
          <span class="icon">📝</span>
          <span>记录</span>
        </button>
        <button class="nav-btn" @click="router.push('/calendar')">
          <span class="icon">📅</span>
          <span>日历</span>
        </button>
        <button class="nav-btn" @click="router.push('/management')">
          <span class="icon">📋</span>
          <span>管理</span>
        </button>
        <button class="nav-btn" @click="router.push('/settings')">
          <span class="icon">⚙️</span>
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
}

.stats-title {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.stats-content {
  padding: var(--spacing-lg) 0;
}

.empty-hint {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
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

.nav-btn .icon {
  font-size: 1.5rem;
}

.footer {
  text-align: center;
  padding: var(--spacing-md) 0;
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
}
</style>
