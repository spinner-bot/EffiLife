<script setup lang="ts">
import { computed } from 'vue'
import { current, dispatch } from '../../application/runtime'
import type { Preferences } from '../../domain/models'
import { themes } from '../../ui/themes'
import { fonts } from '../../ui/fonts'
import { currentLocale, t, errorMessage } from '../../i18n'
import { notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
import { resourceRevision } from '../../extensions/resources'
import { enterSafeMode } from '../../extensions/safe-mode'
const themeList = computed(() => { resourceRevision.value; return themes.values() })
const fontList = computed(() => { resourceRevision.value; return fonts.values() })
function themeName(theme: ReturnType<typeof themes.values>[number]) { return theme.name[currentLocale.value] || theme.name['en-US'] || Object.values(theme.name)[0] }
function themeLabel(theme: ReturnType<typeof themes.values>[number]) { return themeName(theme) + (theme.id >= 100000 ? ' · ' + theme.author + ' · ' + theme.version + ' · #' + theme.id : '') }
async function preferences(value: Partial<Preferences>) {
  try { await dispatch({ type: 'savePreferences', preferences: value }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
</script>
<template>
  <PageHeader :title="t('more.appearance')" />
  <div class="settings-grid">
    <Panel :title="t('settings.font')"><div class="panel-body stack"><label class="field"><span>{{ t('settings.font') }}</span><select :value="current.preferences.fontId" class="select" @change="preferences({ fontId: ($event.target as HTMLSelectElement).value })"><option v-for="font in fontList" :key="font.id" :value="font.id">{{ font.id === 'system' ? t('settings.systemFont') : font.name }}</option></select></label></div></Panel>
    <Panel :title="t('settings.theme')" class="settings-full"><template #actions><UiButton variant="ghost" @click="enterSafeMode">{{ t('extensions.enterSafe') }}</UiButton></template><div class="panel-body theme-grid"><button v-for="theme in themeList" :key="theme.id" type="button" class="theme-option" :aria-label="themeLabel(theme)" :aria-pressed="current.preferences.themeId === theme.id" @click="preferences({ themeId: theme.id })">
      <span class="theme-preview" :style="{ background: theme.palette.background }"><span :style="{ background: theme.palette.surface }" /><span :style="{ background: theme.palette.accent }" /></span><span class="theme-name">{{ themeName(theme) }}<Icon v-if="current.preferences.themeId === theme.id" name="check" :size="15" /></span><span v-if="theme.id >= 100000" class="small muted">{{ theme.author }} · {{ theme.version }} · #{{ theme.id }}</span>
    </button></div></Panel>
  </div>
</template>
