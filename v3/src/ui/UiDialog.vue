<script setup lang="ts">
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription } from 'reka-ui'
import Icon from './Icon.vue'
import UiButton from './UiButton.vue'
import { t } from '../i18n'
defineProps<{ open: boolean; title: string; description?: string }>()
const emit = defineEmits<{ close: [] }>()
</script>
<template>
  <DialogRoot :open="open" @update:open="value => { if (!value) emit('close') }">
    <DialogPortal>
      <DialogOverlay class="dialog-overlay" />
      <DialogContent class="dialog-content">
        <DialogTitle class="dialog-heading">{{ title }}</DialogTitle>
        <DialogDescription :class="description ? 'dialog-description' : 'sr-only'">{{ description || title }}</DialogDescription>
        <UiButton class="dialog-close" variant="ghost" icon :aria-label="t('common.close')" @click="emit('close')"><Icon name="close" /></UiButton>
        <slot />
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

