<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { AlertTriangle, Check, X } from 'lucide-vue-next'
import { activeConfirm, settleConfirm } from '@/services/confirmService'
import { useI18n } from '@/i18n'

const { t } = useI18n()
const cancelButton = ref<HTMLButtonElement | null>(null)

watch(activeConfirm, async (request) => {
  if (!request) return
  await nextTick()
  cancelButton.value?.focus()
})

function close(confirmed: boolean) {
  settleConfirm(confirmed)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div v-if="activeConfirm" class="confirm-backdrop" @click.self="close(false)">
        <section class="confirm-dialog theme-card" :class="{ 'confirm-danger': activeConfirm.tone === 'danger' }" role="alertdialog" aria-modal="true" :aria-labelledby="`confirm-title-${activeConfirm.id}`" @keydown.esc="close(false)">
          <div class="confirm-icon"><AlertTriangle :size="19" /></div>
          <div class="confirm-copy"><h2 :id="`confirm-title-${activeConfirm.id}`">{{ t('common.confirmTitle') }}</h2><p>{{ activeConfirm.message }}</p></div>
          <button class="confirm-close" type="button" :aria-label="t('common.cancel')" @click="close(false)"><X :size="17" /></button>
          <footer class="confirm-actions">
            <button ref="cancelButton" class="confirm-cancel" type="button" @click="close(false)">{{ t('common.cancel') }}</button>
            <button class="confirm-submit" :class="{ danger: activeConfirm.tone === 'danger' }" type="button" @click="close(true)"><Check :size="15" /> {{ t('common.confirm') }}</button>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-backdrop { position: fixed; inset: 0; z-index: 110; display: grid; place-items: center; padding: 20px; background: rgba(8, 12, 24, .45); backdrop-filter: blur(8px); }
.confirm-dialog { position: relative; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 12px; width: min(430px, 100%); border: 1px solid var(--color-border); border-radius: 17px; padding: 22px; box-shadow: var(--shadow-lg, 0 20px 60px rgba(0,0,0,.22)); }
.confirm-icon { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 11px; color: var(--color-primary); background: var(--color-primary-muted); }
.confirm-danger .confirm-icon { color: var(--color-error); background: color-mix(in srgb, var(--color-error) 12%, var(--color-bg-secondary)); }
.confirm-copy { min-width: 0; padding-right: 20px; }
.confirm-copy h2 { margin: 1px 0 7px; color: var(--color-text-primary); font-size: 16px; }
.confirm-copy p { margin: 0; color: var(--color-text-secondary); font-size: 13px; line-height: 1.55; white-space: pre-line; }
.confirm-close { position: absolute; top: 13px; right: 13px; display: grid; place-items: center; border: 0; padding: 5px; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.confirm-close:hover { color: var(--color-text-primary); }
.confirm-actions { grid-column: 1 / -1; display: flex; justify-content: flex-end; gap: 8px; margin-top: 6px; }
.confirm-cancel, .confirm-submit { display: inline-flex; align-items: center; justify-content: center; gap: 5px; border: 1px solid var(--color-border); border-radius: 9px; padding: 8px 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; font-weight: 600; }
.confirm-submit { border-color: var(--color-primary); color: var(--color-button-text); background: var(--color-primary); }
.confirm-submit.danger { border-color: var(--color-error); background: var(--color-error); }
.confirm-cancel:focus-visible, .confirm-submit:focus-visible, .confirm-close:focus-visible { outline: 3px solid var(--color-primary-muted); outline-offset: 2px; }
.confirm-fade-enter-active, .confirm-fade-leave-active { transition: opacity .18s ease; }
.confirm-fade-enter-from, .confirm-fade-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .confirm-fade-enter-active, .confirm-fade-leave-active { transition: none; } }
</style>
