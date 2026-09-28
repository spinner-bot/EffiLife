<script setup lang="ts">
import { X, CheckCircle2, Info, AlertCircle } from 'lucide-vue-next'
import { dismissToast, toastMessages } from '@/services/toastService'
import { useI18n } from '@/i18n'

const { t } = useI18n()
</script>

<template>
  <div class="toast-host" :aria-label="t('app.notifications')">
    <TransitionGroup name="toast" tag="div" class="toast-stack">
      <div
        v-for="toast in toastMessages"
        :key="toast.id"
        class="toast-message"
        :class="`toast-${toast.tone}`"
        :role="toast.tone === 'error' ? 'alert' : 'status'"
        aria-live="polite"
      >
        <CheckCircle2 v-if="toast.tone === 'success'" :size="17" aria-hidden="true" />
        <AlertCircle v-else-if="toast.tone === 'error'" :size="17" aria-hidden="true" />
        <Info v-else :size="17" aria-hidden="true" />
        <span>{{ toast.message }}</span>
        <button type="button" class="toast-close" :aria-label="t('app.closeNotification')" @click="dismissToast(toast.id)">
          <X :size="15" aria-hidden="true" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-host { position: fixed; z-index: 100; right: 20px; bottom: 20px; width: min(390px, calc(100vw - 28px)); pointer-events: none; }
.toast-stack { display: grid; gap: 9px; }
.toast-message { display: flex; align-items: flex-start; gap: 9px; border: 1px solid var(--color-border); border-left: 3px solid var(--color-primary); border-radius: 12px; padding: 11px 10px 11px 12px; color: var(--color-text-primary); background: var(--color-bg-elevated); box-shadow: var(--shadow-lg, 0 10px 25px rgba(0,0,0,.16)); font-size: 13px; line-height: 1.45; pointer-events: auto; }
.toast-message > svg { flex: 0 0 auto; margin-top: 1px; color: var(--color-primary); }
.toast-success { border-left-color: var(--color-success); }
.toast-success > svg { color: var(--color-success); }
.toast-error { border-left-color: var(--color-error); }
.toast-error > svg { color: var(--color-error); }
.toast-close { display: grid; flex: 0 0 auto; place-items: center; margin: -2px 0 0 auto; border: 0; padding: 3px; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.toast-close:hover { color: var(--color-text-primary); }
.toast-enter-active, .toast-leave-active { transition: opacity .2s ease, transform .2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
@media (prefers-reduced-motion: reduce) { .toast-enter-active, .toast-leave-active { transition: opacity .1s linear; } .toast-enter-from, .toast-leave-to { transform: none; } }
@media (max-width: 600px) { .toast-host { right: 14px; bottom: 14px; } }
</style>
