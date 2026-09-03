<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="management-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
        <span>←</span> 返回
      </button>
      <h1>计划管理</h1>
    </header>

    <main class="main-content">
      <section class="info-card">
        <h2>今日计划</h2>
        <p class="plan-name">工作日（切分制）</p>
        <p class="plan-desc">背景类别：睡觉</p>
      </section>

      <section class="action-grid">
        <button class="action-btn">
          <span class="action-icon">📅</span>
          <span>日程安排</span>
        </button>
        <button class="action-btn">
          <span class="action-icon">📋</span>
          <span>日计划管理</span>
        </button>
        <button class="action-btn">
          <span class="action-icon">🔄</span>
          <span>临时计划变更</span>
        </button>
      </section>
    </main>
  </div>
</template>

<style scoped>
.management-view {
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
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.info-card {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
}

.info-card h2 {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.plan-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.plan-desc {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
}

.action-icon {
  font-size: 2rem;
}
</style>
