<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { current } from '../application/runtime'
import type { InstalledPackage } from '../domain/models'
import { builtinDecoration } from '../extensions/builtin-decoration'
import { assertManifest, payloadBytes } from '../extensions/manifest'
import { resourceRevision } from '../extensions/resources'
import { themes } from './themes'
import { safeMode } from '../extensions/safe-mode'
import ExtensionSandbox from './ExtensionSandbox.vue'

const emit = defineEmits<{ layout: [value: boolean] }>()
const builtin = shallowRef<InstalledPackage>()
let sequence = 0
watch(() => current.value.preferences.themeId, async id => {
  const request = ++sequence
  builtin.value = undefined
  if (safeMode || id >= 100000) return
  const theme = themes.get(id)
  const result = theme ? await builtinDecoration(theme) : undefined
  if (request === sequence) builtin.value = result
}, { immediate: true })
const layers = computed(() => {
  resourceRevision.value
  if (safeMode) return []
  const selected = current.value.preferences.themeId
  const entries = current.value.packages.filter(entry => entry.status === 'enabled' && (entry.kind === 'function' || entry.kind === 'theme' && entry.id === selected && themes.get(entry.id)))
  if (builtin.value) entries.push(builtin.value)
  return entries.flatMap(entry => {
    assertManifest(entry.manifest)
    const executable = entry.permissions.some(capability => entry.grants.includes(capability) && ['overlay.canvas', 'overlay.interactive', 'app.layout'].includes(capability))
    if (!executable) return []
    const paths = [entry.manifest.entry, ...(entry.manifest.scripts || [])].filter((path): path is string => Boolean(path))
    const source = [...new Set(paths)].map(path => new TextDecoder().decode(payloadBytes(entry.payload, path))).join('\n;\n')
    if (!source) return []
    const layout = entry.grants.includes('app.layout') && entry.permissions.includes('app.layout')
    const replacement = layout && entry.kind === 'theme'
    return [{ entry, source, layout, replacement, key: entry.kind + ':' + entry.id + ':' + source + ':' + entry.grants.join(','), gradient: entry.source === 'builtin' ? themes.get(entry.id)?.decoration?.gradient?.replace('to-br', 'to bottom right') : undefined }]
  })
})
watch(() => layers.value.find(layer => layer.replacement)?.key, () => emit('layout', false), { immediate: true })
</script>
<template>
  <div v-for="layer in layers" :key="layer.key" :class="layer.replacement ? 'theme-replacement' : layer.layout ? 'extension-widget' : 'theme-decoration'" :style="layer.gradient ? { backgroundImage: layer.gradient } : undefined">
    <ExtensionSandbox :entry="layer.entry" :source="layer.source" @ready="() => { if (layer.replacement) emit('layout', true) }" />
  </div>
</template>

