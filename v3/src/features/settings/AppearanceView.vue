<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { current, dispatch } from '../../application/runtime'
import type { Preferences } from '../../domain/models'
import { surfaceEffects, effectDefaults } from '../../domain/appearance'
import { appearanceFor } from '../../ui/surface-effects'
import AppearanceEditor from './AppearanceEditor.vue'
import { themes, type ThemeDefinition } from '../../ui/themes'
import { fonts } from '../../ui/fonts'
import { currentLocale, t, errorMessage } from '../../i18n'
import { notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
import { resourceRevision } from '../../extensions/resources'
import { enterSafeMode } from '../../extensions/safe-mode'
const advanced = ref(false), editingTheme = shallowRef<ThemeDefinition>()
const activeTheme = computed(() => { resourceRevision.value; return themes.get(current.value.preferences.themeId) || themes.get(1)! })
const appearance = computed(() => appearanceFor(activeTheme.value, current.value.preferences.appearance))
function editAdvanced() { editingTheme.value = activeTheme.value; advanced.value = true }
async function material(effect: string) {
  await preferences({ appearance: { ...current.value.preferences.appearance, [String(activeTheme.value.id)]: { ...appearance.value, effect, parameters: effectDefaults(effect) } } })
}
const themeList = computed(() => { resourceRevision.value; return themes.values() })
const fontList = computed(() => { resourceRevision.value; return fonts.values() })
function themeName(theme: ReturnType<typeof themes.values>[number]) { return theme.name[currentLocale.value] || theme.name['en-US'] || Object.values(theme.name)[0] }
function themeLabel(theme: ReturnType<typeof themes.values>[number]) { return themeName(theme) + (theme.id >= 100000 ? ' · ' + theme.author + ' · ' + theme.version + ' · #' + theme.id : '') }
async function preferences(value: Partial<Preferences>) {
  try { await dispatch({ type: 'savePreferences', preferences: value }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
</script>
<template>
  <PageHeader :title="t('more.appearance')" back="/more" />
  <div class="settings-grid">
    <Panel :title="t('settings.font')"><div class="panel-body stack"><label class="field"><span>{{ t('settings.font') }}</span><select :value="current.preferences.fontId" class="select" @change="preferences({ fontId: ($event.target as HTMLSelectElement).value })"><option v-for="font in fontList" :key="font.id" :value="font.id">{{ font.id === 'system' ? t('settings.systemFont') : font.name }}</option></select></label></div></Panel>
    <Panel :title="t('appearance.material')"><div class="panel-body material-grid"><div v-for="effect in surfaceEffects" :key="effect.id" class="appearance-choice"><button type="button" class="material-option" :class="'material-' + effect.id" :aria-pressed="appearance.effect === effect.id" @click="material(effect.id)"><span class="material-mini"><i /></span><strong>{{ t(effect.label) }}</strong></button><button v-if="appearance.effect === effect.id" type="button" class="advanced-trigger" :aria-label="t('appearance.cardAdvanced')" @click="editAdvanced"><Icon name="settings" :size="15" /><span>{{ t('appearance.advanced') }}</span></button></div></div></Panel>
    <Panel :title="t('settings.theme')" class="settings-full"><template #actions><UiButton variant="ghost" @click="enterSafeMode">{{ t('extensions.enterSafe') }}</UiButton></template><div class="panel-body theme-grid"><div v-for="theme in themeList" :key="theme.id" class="appearance-choice"><button type="button" class="theme-option" :aria-label="themeLabel(theme)" :aria-pressed="current.preferences.themeId === theme.id" @click="preferences({ themeId: theme.id })">
      <span class="theme-preview" :style="{ background: theme.palette.background }"><span :style="{ background: theme.palette.surface }" /><span :style="{ background: theme.palette.accent }" /></span><span class="theme-name">{{ themeName(theme) }}<Icon v-if="current.preferences.themeId === theme.id" name="check" :size="15" /></span><span v-if="theme.id >= 100000" class="small muted">{{ theme.author }} · {{ theme.version }} · #{{ theme.id }}</span>
    </button><button v-if="current.preferences.themeId === theme.id" type="button" class="advanced-trigger theme-advanced" :aria-label="t('appearance.themeAdvanced')" @click="editAdvanced"><Icon name="settings" :size="15" /><span>{{ t('appearance.advanced') }}</span></button></div></div></Panel>
  </div>
  <AppearanceEditor :open="advanced" :theme="editingTheme" @close="advanced = false" />
</template>
<style scoped>
.appearance-choice { position: relative; min-width: 0; }.theme-option { width: 100%; height: 100%; }.advanced-trigger { position: absolute; left: 12px; top: 40px; border: 1px solid var(--line); border-radius: .45rem; padding: .3rem; display: inline-flex; align-items: center; gap: .35rem; color: var(--ink); background: var(--surface); cursor: pointer; box-shadow: 0 2px 8px #0001; }.advanced-trigger span { max-width: 0; opacity: 0; overflow: hidden; white-space: nowrap; transition: max-width 180ms ease,opacity 180ms ease; }.advanced-trigger:hover span,.advanced-trigger:focus-visible span { max-width: 6rem; opacity: 1; }.material-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: .5rem; }.material-option { width: 100%; display: grid; gap: .6rem; padding: .5rem; border: 1px solid var(--line); border-radius: .75rem; background: transparent; color: var(--ink); cursor: pointer; }.material-option[aria-pressed=true] { border-color: var(--accent); outline: 1px solid var(--accent); }.material-option strong { font-size: var(--text-xs); }.material-mini { display: grid; place-items: center; height: 60px; background: radial-gradient(ellipse at 30% 20%,var(--accent),var(--subtle)); border-radius: .4rem; overflow: hidden; }.material-mini i { width: 75%; height: 65%; border-radius: .4rem; background: var(--surface); }.material-glass .material-mini i { background: color-mix(in srgb,var(--surface) 55%,transparent); backdrop-filter: blur(4px); }.material-frosted .material-mini i { background: color-mix(in srgb,var(--surface) 80%,transparent); backdrop-filter: blur(12px) saturate(70%); }.theme-advanced { top: 45px; }
@media(prefers-reduced-motion:reduce) { .advanced-trigger span { transition: none; } }
</style>
