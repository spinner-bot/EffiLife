<script setup lang="ts">
import { computed } from 'vue'
import { EventSystem } from './EventSystem'
import { X } from 'lucide-vue-next'
import type { AppEvent } from './EventSystem'

const events = computed(() => EventSystem.getActiveEvents())

function dismissEvent(eventId: string) {
  EventSystem.dismissEvent(eventId)
}

function getEventStyle(event: AppEvent) {
  switch (event.type) {
    case 'plan_complete_100':
      return 'achievement'
    case 'plan_complete_90':
      return 'success'
    case 'plan_low_progress':
      return 'warning'
    default:
      return 'info'
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="event-popup-container">
      <TransitionGroup name="popup">
        <div
          v-for="event in events"
          :key="event.id"
          class="event-popup"
          :class="getEventStyle(event)"
        >
          <div class="popup-icon">
            {{ event.icon || '🔔' }}
          </div>
          <div class="popup-content">
            <h3 class="popup-title">{{ event.title }}</h3>
            <p class="popup-message">{{ event.message }}</p>
          </div>
          <button class="popup-close" @click="dismissEvent(event.id)">
            <X :size="16" />
          </button>
          <div class="popup-progress"></div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.event-popup-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.event-popup {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  min-width: 320px;
  max-width: 400px;
  border-radius: 12px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  pointer-events: auto;
  position: relative;
  overflow: hidden;
}

.event-popup.achievement {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-color: #ffd700;
}

.event-popup.achievement .popup-title {
  color: #ffd700;
}

.event-popup.success {
  background: linear-gradient(135deg, #1a2e1a 0%, #163e16 100%);
  border-color: #4ade80;
}

.event-popup.success .popup-title {
  color: #4ade80;
}

.event-popup.warning {
  background: linear-gradient(135deg, #2e2a1a 0%, #3e3216 100%);
  border-color: #fbbf24;
}

.event-popup.warning .popup-title {
  color: #fbbf24;
}

.event-popup.info {
  background: linear-gradient(135deg, #1a1a2e 0%, #16283e 100%);
  border-color: #60a5fa;
}

.event-popup.info .popup-title {
  color: #60a5fa;
}

.popup-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.popup-content {
  flex: 1;
  min-width: 0;
}

.popup-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--color-text-primary);
}

.popup-message {
  font-size: 14px;
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.popup-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.popup-close:hover {
  background: rgba(255, 255, 255, 0.2);
  color: var(--color-text-primary);
}

.popup-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: currentColor;
  opacity: 0.5;
  animation: progress 5s linear forwards;
}

@keyframes progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

/* Transition animations */
.popup-enter-active {
  animation: slideIn 0.3s ease-out;
}

.popup-leave-active {
  animation: slideOut 0.3s ease-in;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .event-popup {
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  }
}
</style>
