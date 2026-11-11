<script setup lang="ts">
import UiDialog from './UiDialog.vue'
import UiButton from './UiButton.vue'
import Icon from './Icon.vue'
import { notices, dismiss, confirmation, finishConfirmation } from './state'
import { t } from '../i18n'
</script>
<template>
  <div class="toast-host" aria-live="polite" aria-relevant="additions">
    <div v-for="notice in notices" :key="notice.id" class="toast" :class="notice.kind" :role="notice.kind === 'error' ? 'alert' : 'status'">
      <Icon :name="notice.kind" /><span class="grow">{{ notice.message }}</span>
      <UiButton variant="ghost" icon :aria-label="t('common.close')" @click="dismiss(notice.id)"><Icon name="close" :size="16" /></UiButton>
    </div>
  </div>
  <UiDialog :open="Boolean(confirmation)" :title="confirmation?.title || ''" :description="confirmation?.description || undefined" @close="finishConfirmation(false)">
    <div class="dialog-footer">
      <UiButton @click="finishConfirmation(false)">{{ t('common.cancel') }}</UiButton>
      <UiButton variant="primary" @click="finishConfirmation(true)">{{ t('common.confirm') }}</UiButton>
    </div>
  </UiDialog>
</template>

