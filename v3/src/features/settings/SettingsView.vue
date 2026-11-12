<script setup lang="ts">
import { computed } from 'vue'
import { current, dispatch } from '../../application/runtime'
import type { Preferences } from '../../domain/models'
import { locales, t, errorMessage } from '../../i18n'
import { notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import ArchiveTools from './ArchiveTools.vue'
import HeaderClockSettings from './HeaderClockSettings.vue'
import PackageTools from './PackageTools.vue'
import { resourceRevision } from '../../extensions/resources'
const version = __APP_VERSION__
const timeZones = Intl.supportedValuesOf('timeZone')
const localeList = computed(() => { resourceRevision.value; return locales.values() })
async function preferences(value: Partial<Preferences>) {
  try { await dispatch({ type: 'savePreferences', preferences: value }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
</script>
<template>
  <PageHeader :title="t('settings.title')" :subtitle="t('settings.subtitle')" />
  <div class="settings-grid">
    <Panel :title="t('settings.language')"><div class="panel-body stack">
      <label class="field"><span>{{ t('settings.language') }}</span><select :value="current.preferences.locale" class="select" @change="preferences({ locale: ($event.target as HTMLSelectElement).value })"><option v-for="locale in localeList" :key="locale.id" :value="locale.id">{{ locale.name }}</option></select></label>
      <label class="field"><span>{{ t('form.timezone') }}</span><input :value="current.preferences.timeZone" list="time-zone-options" class="input" @change="preferences({ timeZone: ($event.target as HTMLInputElement).value })" /><datalist id="time-zone-options"><option v-for="zone in timeZones" :key="zone" :value="zone" /></datalist></label>
    </div></Panel>
    <div class="stack"><Panel :title="t('settings.data')"><div class="panel-body"><ArchiveTools /></div></Panel><Panel :title="t('settings.about')"><div class="panel-body stack"><strong>EffiLife</strong><p class="muted small">{{ t('settings.version', { version }) }} · {{ t('app.tagline') }}</p></div></Panel></div>
    <HeaderClockSettings />
    <PackageTools />
  </div>
</template>
