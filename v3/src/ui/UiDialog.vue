<script setup lang="ts">
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription } from 'reka-ui'
import Icon from './Icon.vue'
import UiButton from './UiButton.vue'
import { t } from '../i18n'
import { useDialogLayer } from './dialog-layers'
const props = defineProps<{ open: boolean; title: string; description?: string }>()
const emit = defineEmits<{ close: [] }>()
const { overlay, content } = useDialogLayer(() => props.open)
let opener: HTMLElement | null = null
function focusInput(event: Event) {
  const content = event.target
  if (!(content instanceof HTMLElement)) return
  opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
  const editable = content.querySelector<HTMLElement>('input:not([type=checkbox]):not([type=hidden]):not([disabled]), textarea:not([disabled])')
  const fallback = content.querySelector<HTMLElement>('select:not([disabled]), button:not(.dialog-close):not([disabled])')
  const target = editable || fallback
  if (target) { event.preventDefault(); target.focus({ preventScroll: true }) }
}
function restoreFocus(event: Event) {
  event.preventDefault()
  const target = opener
  // Nested confirmations unmount before the underlying dialog. Restore only
  // targets still in the document, after Reka has removed the inner focus scope.
  requestAnimationFrame(() => { if (target?.isConnected) target.focus({ preventScroll: true }) })
}
</script>
<template>
  <DialogRoot :open="open" @update:open="value => { if (!value) emit('close') }">
    <DialogPortal>
      <DialogOverlay class="dialog-overlay" :style="overlay" />
      <DialogContent class="dialog-content" :style="content" @open-auto-focus="focusInput" @close-auto-focus="restoreFocus">
        <DialogTitle class="dialog-heading">{{ title }}</DialogTitle>
        <DialogDescription :class="description ? 'dialog-description' : 'sr-only'">{{ description || title }}</DialogDescription>
        <UiButton class="dialog-close" variant="ghost" icon :aria-label="t('common.close')" @click="emit('close')"><Icon name="close" /></UiButton>
        <slot />
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

