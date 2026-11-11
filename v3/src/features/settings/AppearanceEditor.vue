<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { current, dispatch } from '../../application/runtime'
import { defaultAppearance, effectDefaults, surfaceEffects } from '../../domain/appearance'
import { appearanceFor, surfaceTokens } from '../../ui/surface-effects'
import type { ThemeDefinition } from '../../ui/themes'
import { t, currentLocale, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
const props = defineProps<{ open: boolean; theme?: ThemeDefinition }>()
const emit = defineEmits<{ close: [] }>()
const draft = reactive(defaultAppearance()), error = ref(''), busy = ref(false)
let initial = ''
const fields = computed(() => surfaceEffects.find(effect => effect.id === draft.effect)!.parameters)
const name = computed(() => props.theme?.name[currentLocale.value] || props.theme?.name['en-US'] || '')
const hasAnimation = computed(() => props.theme && props.theme.id < 100000 && Boolean(props.theme.decoration))
const hasDensity = computed(() => Boolean(props.theme?.decoration?.particles || props.theme?.decoration?.ambient))
watch(() => props.open, open => {
  if (!open || !props.theme) return
  Object.assign(draft, appearanceFor(props.theme, current.value.preferences.appearance)); error.value = ''; initial = JSON.stringify(draft)
})
function effect(id: string) { draft.effect = id; draft.parameters = effectDefaults(id) }
function reset() { if (props.theme) Object.assign(draft, appearanceFor(props.theme)) }
async function close() {
  if (busy.value) return
  if (JSON.stringify(draft) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  if (!props.theme) return
  busy.value = true
  try { await dispatch({ type: 'savePreferences', preferences: { appearance: { ...current.value.preferences.appearance, [String(props.theme.id)]: structuredClone(draft) } } }); emit('close') } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="open" :title="t('appearance.advanced') + ' · ' + name" :description="t('appearance.scope')" @close="close"><form class="stack" @submit.prevent="save">
    <div class="material-preview" :style="{ background: theme?.palette.background, ...surfaceTokens(draft) }"><div class="material-preview-light" :style="{ background: theme?.palette.accent }" /><div class="appearance-sample"><strong>{{ t('appearance.previewTitle') }}</strong><p class="small muted">{{ t('appearance.previewHelp') }}</p></div></div>
    <label class="field"><span>{{ t('appearance.material') }}</span><select class="select" :value="draft.effect" @change="effect(($event.target as HTMLSelectElement).value)"><option v-for="item in surfaceEffects" :key="item.id" :value="item.id">{{ t(item.label) }}</option></select></label>
    <label v-for="field in fields" :key="field.key" class="field"><span class="cluster spread">{{ t(field.label) }}<output>{{ draft.parameters[field.key] }}</output></span><input v-model.number="draft.parameters[field.key]" type="range" :min="field.min" :max="field.max" :step="field.step" :aria-label="t(field.label)" /></label>
    <fieldset v-if="hasAnimation" class="appearance-animation stack"><legend>{{ t('appearance.animation') }}</legend><label class="check-field"><input v-model="draft.animation.enabled" type="checkbox" />{{ t('appearance.enabled') }}</label><template v-if="draft.animation.enabled"><label class="field"><span class="cluster spread">{{ t('appearance.speed') }}<output>{{ draft.animation.speed }}×</output></span><input v-model.number="draft.animation.speed" type="range" min="0.2" max="2" step="0.05" :aria-label="t('appearance.speed')" /></label><label class="field"><span class="cluster spread">{{ t('appearance.intensity') }}<output>{{ Math.round(draft.animation.intensity * 100) }}%</output></span><input v-model.number="draft.animation.intensity" type="range" min="0" max="1" step="0.01" :aria-label="t('appearance.intensity')" /></label><label v-if="hasDensity" class="field"><span class="cluster spread">{{ t('appearance.density') }}<output>{{ draft.animation.density }}×</output></span><input v-model.number="draft.animation.density" type="range" min="0.2" max="2" step="0.1" :aria-label="t('appearance.density')" /></label></template><p class="small muted">{{ t('appearance.reducedMotion') }}</p></fieldset>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p><div class="dialog-footer"><UiButton :disabled="busy" @click="reset">{{ t('appearance.reset') }}</UiButton><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton variant="primary" type="submit" :disabled="busy">{{ t('common.save') }}</UiButton></div>
  </form></UiDialog>
</template>
<style scoped>
.material-preview { position: relative; overflow: hidden; padding: 2rem; border-radius: 1rem; }.material-preview-light { position: absolute; width: 65%; height: 120%; top: -20%; left: 25%; border-radius: 50%; opacity: .35; filter: blur(24px); }.appearance-sample { position: relative; padding: 1rem; border: 1px solid var(--line); background: var(--card-surface); backdrop-filter: var(--card-filter); -webkit-backdrop-filter: var(--card-filter); border-radius: var(--card-radius); box-shadow: var(--card-shadow); }.appearance-animation { border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 1rem; }.appearance-animation legend { padding-inline: .4rem; font-size: var(--text-sm); }input[type=range] { width: 100%; accent-color: var(--accent); }
</style>
