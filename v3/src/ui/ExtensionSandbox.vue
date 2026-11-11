<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { InstalledPackage } from '../domain/models'
import { current, dispatch, service } from '../application/runtime'
import { sandboxBridge } from '../application/sandbox-bridge'
import { SandboxSession } from '../extensions/sandbox-session'
import { effectiveCapabilities, isCapability } from '../extensions/capabilities'
import { assertManifest, payloadBytes } from '../extensions/manifest'
import { themes, themeTokens } from './themes'
import { notify } from './state'
import { t } from '../i18n'

const props = defineProps<{ entry: InstalledPackage; source: string }>()
const emit = defineEmits<{ ready: [] }>()
const container = ref<HTMLElement>()
const router = useRouter()
let session: SandboxSession | undefined
onMounted(() => {
  const entry = props.entry
  assertManifest(entry.manifest)
  const granted = effectiveCapabilities(entry.manifest.permissions, entry.grants.filter(isCapability))
  const request = entry.source === 'builtin' ? async () => { throw new Error('builtin decoration has no application API') } : sandboxBridge({ kind: entry.kind as 'theme' | 'function', packageId: entry.id, checksum: entry.checksum! }, { service, dispatch, navigate: path => { router.push(path) } })
  session = new SandboxSession(container.value!, {
    source: props.source, capabilities: granted, title: entry.name,
    theme: themeTokens(themes.get(current.value.preferences.themeId) || themes.get(1)!),
    request, ready: () => emit('ready'),
    failure: async code => {
      if (entry.source === 'local') await dispatch({ type: 'packageRuntimeFailure', kind: entry.kind as 'theme' | 'function', packageId: entry.id, checksum: entry.checksum!, detail: code }).catch(() => {})
      else await dispatch({ type: 'savePreferences', preferences: { themeId: 1 } }).catch(() => {})
      notify(t(code) === code ? t('extensions.scriptFailed') : t(code), 'error')
    },
  })
})
watch(() => current.value.preferences.themeId, id => session?.update(themeTokens(themes.get(id) || themes.get(1)!)))
watch(() => current.value.revision, revision => {
  if (props.entry.grants.includes('app.events')) session?.update({ ...themeTokens(themes.get(current.value.preferences.themeId) || themes.get(1)!), revision: String(revision) })
})
onBeforeUnmount(() => session?.dispose())
</script>
<template><div ref="container" class="extension-sandbox" /></template>

