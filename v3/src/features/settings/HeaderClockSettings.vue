<script setup lang="ts">
import { computed } from 'vue'
import { current, dispatch } from '../../application/runtime'
import { defaultHeaderClock } from '../../domain/preferences'
import type { HeaderClockPreferences } from '../../domain/models'
import { t, errorMessage } from '../../i18n'
import { notify } from '../../ui/state'
import Panel from '../../ui/Panel.vue'
const options = computed(() => current.value.preferences.headerClock || defaultHeaderClock)
async function save(value: Partial<HeaderClockPreferences>) {
  try { await dispatch({ type: 'savePreferences', preferences: { headerClock: { ...options.value, ...value } } }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
</script>
<template>
  <Panel :title="t('clock.title')"><div class="panel-body stack">
    <label class="field"><span>{{ t('clock.display') }}</span><select class="select" :value="options.display" @change="save({ display: ($event.target as HTMLSelectElement).value as HeaderClockPreferences['display'] })"><option v-for="mode in ['date','time','both']" :key="mode" :value="mode">{{ t('clock.' + mode) }}</option></select></label>
    <label class="field"><span>{{ t('clock.hourCycle') }}</span><select class="select" :value="options.hourCycle" :disabled="options.display === 'date'" @change="save({ hourCycle: Number(($event.target as HTMLSelectElement).value) as 12 | 24 })"><option :value="24">{{ t('clock.24') }}</option><option :value="12">{{ t('clock.12') }}</option></select></label>
    <label class="check-field"><input type="checkbox" :checked="options.showPeriod" :disabled="options.hourCycle === 24 || options.display === 'date'" @change="save({ showPeriod: ($event.target as HTMLInputElement).checked })" />{{ t('clock.showPeriod') }}</label>
    <label class="field"><span>{{ t('clock.align') }}</span><select class="select" :value="options.align" @change="save({ align: ($event.target as HTMLSelectElement).value as HeaderClockPreferences['align'] })"><option value="right">{{ t('clock.right') }}</option><option value="center">{{ t('clock.center') }}</option></select></label>
  </div></Panel>
</template>
