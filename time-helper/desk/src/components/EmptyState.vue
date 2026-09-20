<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'

interface Props {
  icon?: Component
  title: string
  description?: string
  actionText?: string
  actionRoute?: string
}

const props = withDefaults(defineProps<Props>(), {
  icon: undefined,
  description: '',
  actionText: '',
  actionRoute: '',
})

const emit = defineEmits<{
  (e: 'action'): void
}>()

const hasAction = computed(() => props.actionText && props.actionRoute)

function handleClick() {
  emit('action')
}
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon-wrapper" v-if="icon">
      <component :is="icon" :size="56" class="empty-icon" />
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-description" v-if="description">{{ description }}</p>
    <router-link
      v-if="hasAction"
      :to="actionRoute!"
      class="empty-action-btn"
      @click="handleClick"
    >
      {{ actionText }}
    </router-link>
    <button
      v-else-if="actionText"
      class="empty-action-btn"
      @click="handleClick"
    >
      {{ actionText }}
    </button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl) var(--spacing-lg);
  text-align: center;
  animation: emptyFadeIn 0.4s ease-out;
}

@keyframes emptyFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96px;
  height: 96px;
  border-radius: var(--radius-full);
  background: var(--color-bg-secondary);
  margin-bottom: var(--spacing-lg);
}

.empty-icon {
  color: var(--color-text-tertiary);
  opacity: 0.5;
}

.empty-title {
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  line-height: 1.4;
}

.empty-description {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0 0 var(--spacing-lg) 0;
  max-width: 300px;
  line-height: 1.5;
}

.empty-action-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all var(--transition-fast);
}

.empty-action-btn:hover {
  background: var(--color-primary-hover);
  color: white;
  transform: scale(1.02);
}

.empty-action-btn:active {
  transform: scale(0.98);
}
</style>
