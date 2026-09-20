<script setup lang="ts">
interface Props {
  type?: 'card' | 'list' | 'text'
  count?: number
  animated?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'card',
  count: 3,
  animated: true,
})
</script>

<template>
  <div class="skeleton-loader" :class="[`skeleton-${type}`, { 'is-animated': animated }]">
    <!-- Card 类型 -->
    <template v-if="type === 'card'">
      <div v-for="i in count" :key="i" class="skeleton-card">
        <div class="skeleton-line header"></div>
        <div class="skeleton-line content"></div>
        <div class="skeleton-line content short"></div>
      </div>
    </template>

    <!-- List 类型 -->
    <template v-else-if="type === 'list'">
      <div v-for="i in count" :key="i" class="skeleton-list-item">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-list-body">
          <div class="skeleton-line title"></div>
          <div class="skeleton-line subtitle"></div>
        </div>
      </div>
    </template>

    <!-- Text 类型 -->
    <template v-else-if="type === 'text'">
      <div v-for="i in count" :key="i" class="skeleton-text-block">
        <div class="skeleton-line text"></div>
        <div class="skeleton-line text"></div>
        <div class="skeleton-line text short"></div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.skeleton-loader {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  width: 100%;
}

/* 脉冲动画 */
.is-animated .skeleton-line,
.is-animated .skeleton-avatar {
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-secondary) 40%,
    var(--color-bg-tertiary) 80%
  );
  background-size: 200% 100%;
  animation: skeletonShimmer 1.4s ease-in-out infinite;
}

@keyframes skeletonShimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.skeleton-line {
  height: 12px;
  border-radius: var(--radius-sm);
  background: var(--color-bg-tertiary);
}

.skeleton-line.header {
  height: 16px;
  width: 60%;
  margin-bottom: var(--spacing-sm);
}

.skeleton-line.content {
  width: 100%;
  margin-bottom: var(--spacing-xs);
}

.skeleton-line.content.short {
  width: 40%;
}

.skeleton-line.title {
  height: 14px;
  width: 70%;
  margin-bottom: var(--spacing-xs);
}

.skeleton-line.subtitle {
  height: 12px;
  width: 50%;
}

.skeleton-line.text {
  width: 100%;
  margin-bottom: var(--spacing-xs);
}

.skeleton-line.text.short {
  width: 60%;
}

/* Card 骨架 */
.skeleton-card {
  padding: var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

/* List 骨架 */
.skeleton-list-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: var(--color-bg-tertiary);
  flex-shrink: 0;
}

.skeleton-list-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

/* Text 骨架 */
.skeleton-text-block {
  padding: var(--spacing-sm) 0;
}
</style>
