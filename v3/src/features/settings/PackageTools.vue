<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { current, dispatch } from '../../application/runtime'
import type { InstalledPackage } from '../../domain/models'
import { inspectExtension } from '../../adapters/extension-package'
import { checkImportInput } from '../../extensions/import-budget'
import { acceptedExtensions } from '../../extensions/formats'
import { capabilities, defaultGrants, isCapability, type Capability } from '../../extensions/capabilities'
import { assertManifest, type PackageCandidate } from '../../extensions/manifest'
import { resourceFailures } from '../../extensions/resources'
import { t, currentLocale, errorMessage } from '../../i18n'
import { confirmAction, notify } from '../../ui/state'
import Panel from '../../ui/Panel.vue'
import UiButton from '../../ui/UiButton.vue'
import UiDialog from '../../ui/UiDialog.vue'
import Icon from '../../ui/Icon.vue'

const input = ref<HTMLInputElement>()
const preview = shallowRef<PackageCandidate>()
const editing = shallowRef<InstalledPackage>()
const grants = ref<Capability[]>([])
const updateId = ref('')
const busy = ref(false)
const error = ref('')
let operationId = ''
const accept = ['theme', 'resource', 'function'].flatMap(kind => acceptedExtensions(kind as 'theme' | 'resource' | 'function')).map(extension => '.' + extension).join(',')
const manifest = computed(() => {
  if (preview.value) return preview.value.manifest
  if (!editing.value) return undefined
  assertManifest(editing.value.manifest)
  return editing.value.manifest
})
const duplicates = computed(() => current.value.packages.filter(entry => entry.kind === preview.value?.manifest.type && entry.author === preview.value.manifest.author && entry.name === (preview.value.manifest.name['en-US'] || Object.values(preview.value.manifest.name)[0])))
const audit = computed(() => [...(current.value.extensionAudit || [])].reverse().slice(0, 20))
function name(entry: InstalledPackage) {
  const value = entry.manifest.name as Record<string, string>
  return value[currentLocale.value] || value['en-US'] || entry.name
}
function failure(entry: InstalledPackage) { return resourceFailures.value.find(item => item.kind === entry.kind && item.id === entry.id) }
async function read(event: Event) {
  const target = event.target as HTMLInputElement, file = target.files?.[0]
  if (!file) return
  busy.value = true
  try {
    checkImportInput(file.size)
    preview.value = await inspectExtension(new Uint8Array(await file.arrayBuffer()), __APP_VERSION__)
    grants.value = defaultGrants(preview.value.manifest.permissions)
    updateId.value = ''; error.value = ''; operationId = crypto.randomUUID()
  } catch (failure) { notify(errorMessage(failure), 'error') }
  finally { busy.value = false; target.value = '' }
}
function edit(entry: InstalledPackage) {
  editing.value = entry; preview.value = undefined
  grants.value = entry.grants.filter(isCapability)
  error.value = ''; operationId = crypto.randomUUID()
}
function close() { if (!busy.value) { preview.value = undefined; editing.value = undefined } }
async function save() {
  if (!manifest.value) return
  const added = grants.value.filter(capability => !editing.value?.grants.includes(capability))
  if (added.some(capability => capabilities[capability].level === 3) && !await confirmAction(t('extensions.trustTitle'), t('extensions.trustBody'))) return
  busy.value = true; error.value = ''
  try {
    if (preview.value) await dispatch({ type: 'installPackage', candidate: preview.value, grants: grants.value, updateId: updateId.value ? Number(updateId.value) : undefined }, operationId)
    else if (editing.value) await dispatch({ type: 'setPackageGrants', kind: editing.value.kind as 'theme' | 'resource' | 'function', packageId: editing.value.id, grants: grants.value }, operationId)
    preview.value = undefined; editing.value = undefined
    notify(t('extensions.saved'))
  } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
async function toggle(entry: InstalledPackage) {
  busy.value = true
  try { await dispatch({ type: 'setPackageStatus', kind: entry.kind as 'theme' | 'resource' | 'function', packageId: entry.id, enabled: entry.status !== 'enabled' }) }
  catch (failure) { notify(errorMessage(failure), 'error') } finally { busy.value = false }
}
async function remove(entry: InstalledPackage) {
  if (!await confirmAction(t('extensions.removeTitle', { name: name(entry) }), t('extensions.removeBody'))) return
  busy.value = true
  try { await dispatch({ type: 'removePackage', kind: entry.kind as 'theme' | 'resource' | 'function', packageId: entry.id }) }
  catch (failure) { notify(errorMessage(failure), 'error') } finally { busy.value = false }
}
</script>
<template>
  <Panel :title="t('extensions.title')" class="settings-full">
    <template #actions><UiButton :disabled="busy" @click="input?.click()"><Icon name="plus" :size="17" />{{ t('extensions.install') }}</UiButton></template>
    <input ref="input" type="file" :accept="accept" class="sr-only" tabindex="-1" :aria-label="t('extensions.install')" @change="read" />
    <div v-if="!current.packages.length" class="panel-body"><p class="muted small">{{ t('extensions.empty') }}</p></div>
    <div v-for="entry in current.packages" :key="entry.kind + ':' + entry.id" class="list-row" style="flex-wrap: wrap">
      <div class="grow"><strong>{{ name(entry) }}</strong><p class="small muted">{{ entry.author }} · {{ entry.version }} · {{ t('extensions.kind.' + entry.kind) }} · #{{ entry.id }}</p><p class="small" :class="failure(entry) ? 'form-error' : 'muted'">{{ failure(entry) ? errorMessage(failure(entry)) : t('extensions.status.' + entry.status) }}</p></div>
      <div class="cluster"><UiButton :disabled="busy" @click="edit(entry)">{{ t('extensions.permissions') }}</UiButton><UiButton :disabled="busy" @click="toggle(entry)">{{ t(entry.status === 'enabled' ? 'extensions.disable' : 'extensions.enable') }}</UiButton><UiButton :disabled="busy" variant="ghost" :aria-label="t('common.delete') + ': ' + name(entry)" @click="remove(entry)"><Icon name="delete" :size="17" /></UiButton></div>
    </div>
    <details v-if="audit.length" class="panel-body"><summary>{{ t('extensions.audit') }}</summary><div v-for="entry in audit" :key="entry.id" class="list-row small"><span class="grow">{{ t('extensions.action.' + entry.action) }} · {{ t('extensions.kind.' + entry.kind) }} #{{ entry.packageId }}</span><time class="muted" :datetime="entry.occurredAt">{{ new Date(entry.occurredAt).toLocaleString(currentLocale, { timeZone: current.preferences.timeZone }) }}</time></div></details>
  </Panel>
  <UiDialog :open="Boolean(preview || editing)" :title="preview ? t('extensions.preview') : t('extensions.permissions')" :description="t('extensions.permissionBody')" @close="close">
    <form v-if="manifest" class="stack" @submit.prevent="save">
      <div><h3>{{ manifest.name[currentLocale] || manifest.name['en-US'] || Object.values(manifest.name)[0] }}</h3><p class="muted small">{{ manifest.author }} · {{ manifest.version }} · {{ manifest.license }}</p></div>
      <label v-if="preview && duplicates.length" class="field"><span>{{ t('extensions.duplicate') }}</span><select v-model="updateId" class="select"><option value="">{{ t('extensions.parallel') }}</option><option v-for="entry in duplicates" :key="entry.id" :value="String(entry.id)">{{ t('extensions.upgrade', { version: entry.version, id: entry.id }) }}</option></select></label>
      <div v-for="capability in manifest.permissions" :key="capability" class="stack" style="gap: 4px">
        <label class="check-field"><input v-model="grants" type="checkbox" :value="capability" /><strong>{{ t('capability.' + capability) }}</strong><span class="small muted">L{{ capabilities[capability].level }}{{ manifest.requiredPermissions.includes(capability) ? ' · ' + t('extensions.required') : '' }}</span></label>
        <p v-if="capabilities[capability].writes" class="small muted">{{ t('extensions.writeScope') }}</p>
      </div>
      <p v-if="error" role="alert" class="form-error">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ preview ? t('extensions.confirmInstall') : t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

