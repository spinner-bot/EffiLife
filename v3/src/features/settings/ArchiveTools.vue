<script setup lang="ts">
import { ref, shallowRef } from 'vue'
import type { ArchivePreview } from '../../adapters/archive'
import { inspectArchive, exportArchive } from '../../adapters/archive'
import { current, workspace, service, refresh } from '../../application/runtime'
import { acceptedExtensions } from '../../extensions/formats'
import { saveDataFile } from '../../platform/files'
import { t, errorMessage } from '../../i18n'
import { notify, confirmAction } from '../../ui/state'
import UiButton from '../../ui/UiButton.vue'
import UiDialog from '../../ui/UiDialog.vue'
import Icon from '../../ui/Icon.vue'
defineProps<{ recovery?: boolean }>()
const input = ref<HTMLInputElement>()
const preview = shallowRef<ArchivePreview>()
const error = ref('')
const busy = ref(false)
const accept = [...acceptedExtensions('data'), 'json'].map(extension => '.' + extension).join(',')
async function exportData() {
  busy.value = true
  try {
    const file = await exportArchive(current.value, __APP_VERSION__)
    if (await saveDataFile(file.bytes, file.filename)) notify(t('settings.exported'))
  } catch (failure) { notify(errorMessage(failure), 'error') } finally { busy.value = false }
}
async function readFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  busy.value = true; error.value = ''
  try { preview.value = await inspectArchive(new Uint8Array(await file.arrayBuffer()), __APP_VERSION__, current.value.preferences.timeZone) } catch (failure) { notify(errorMessage(failure), 'error') } finally { busy.value = false; target.value = '' }
}
async function importData() {
  if (!preview.value) return
  busy.value = true
  try { await service.replace(preview.value.workspace); await refresh(); preview.value = undefined; notify(t('settings.imported')) } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
async function restore() {
  if (!await confirmAction(t('settings.restore'), t('settings.restoreConfirm'))) return
  busy.value = true
  try { await service.restoreBackup(); await refresh(); notify(t('settings.restored')) } catch (failure) { notify(errorMessage(failure), 'error') } finally { busy.value = false }
}
function warning(key: string) { const message = t(key); return message === key ? t('settings.migrationGeneral') : message }
</script>
<template>
  <div class="stack" :aria-busy="busy">
    <div class="cluster"><UiButton v-if="!recovery" :disabled="busy || !workspace" @click="exportData"><Icon name="download" :size="18" />{{ t('settings.export') }}</UiButton><UiButton :disabled="busy" @click="input?.click()"><Icon name="upload" :size="18" />{{ t('settings.import') }}</UiButton><UiButton :disabled="busy" variant="ghost" @click="restore"><Icon name="restore" :size="18" />{{ t('settings.restore') }}</UiButton></div>
    <input ref="input" type="file" :accept="accept" class="sr-only" tabindex="-1" :aria-label="t('settings.import')" @change="readFile" />
  </div>
  <UiDialog :open="Boolean(preview)" :title="t('settings.importTitle')" :description="t('settings.importBody')" @close="() => { if (!busy) preview = undefined }">
    <div v-if="preview" class="stack">
      <p class="notice">{{ t('settings.importCounts', { ...preview.counts, plans: preview.counts.plans + preview.counts.archivedPlans }) }}</p>
      <div v-if="preview.warnings.length" class="stack"><h3>{{ t('settings.importWarnings') }}</h3><ul class="muted small"><li v-for="item in preview.warnings" :key="item">{{ warning(item) }}</li></ul></div>
      <p v-if="error" role="alert" class="form-error">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="preview = undefined">{{ t('common.cancel') }}</UiButton><UiButton variant="primary" :disabled="busy" @click="importData">{{ t('settings.importConfirm') }}</UiButton></div>
    </div>
  </UiDialog>
</template>

