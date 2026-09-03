<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="calendar-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
        <span>←</span> 返回
      </button>
      <h1>日历</h1>
    </header>

    <main class="main-content">
      <div class="calendar-placeholder">
        <p>日历视图（待实现）</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.calendar-view {
  min-height: 100vh;
  padding: var(--spacing-lg);
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
}

.back-btn:hover {
  background: var(--color-bg-tertiary);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  max-width: 1000px;
  margin: 0 auto;
}

.calendar-placeholder {
  text-align: center;
  padding: var(--spacing-2xl);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  color: var(--color-text-tertiary);
}
</style>
