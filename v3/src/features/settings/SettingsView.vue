<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { current, dispatch } from '../../application/runtime'
import type { Preferences } from '../../domain/models'
import { themes } from '../../ui/themes'
import { fonts } from '../../ui/fonts'
import { locales, currentLocale, t, categoryName, errorMessage } from '../../i18n'
import { notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import UiButton from '../../ui/UiButton.vue'
import UiDialog from '../../ui/UiDialog.vue'
import Icon from '../../ui/Icon.vue'
import ArchiveTools from './ArchiveTools.vue'
import PackageTools from './PackageTools.vue'
import { resourceRevision } from '../../extensions/resources'

const version = __APP_VERSION__
const busy = ref(false)
const error = ref('')
const categoryOpen = ref(false)
const form = reactive({ categoryId: '', name: '', color: '#526ac9', difficulty: 5 })
const timeZones = Intl.supportedValuesOf('timeZone')
const themeList = computed(() => { resourceRevision.value; return themes.values() })
const fontList = computed(() => { resourceRevision.value; return fonts.values() })
const localeList = computed(() => { resourceRevision.value; return locales.values() })
async function preferences(value: Partial<Preferences>) {
  try { await dispatch({ type: 'savePreferences', preferences: value }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
function addCategory() { Object.assign(form, { categoryId: '', name: '', color: '#526ac9', difficulty: 5 }); error.value = ''; categoryOpen.value = true }
function editCategory(id: string) {
  const category = current.value.categories.find(item => item.id === id)!
  Object.assign(form, { categoryId: id, name: categoryName(category), color: category.color, difficulty: category.difficulty })
  error.value = ''; categoryOpen.value = true
}
async function saveCategory() {
  busy.value = true
  try { await dispatch({ ...form, type: 'saveCategory', categoryId: form.categoryId || undefined }); categoryOpen.value = false } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <PageHeader :title="t('settings.title')" :subtitle="t('settings.subtitle')" />
  <div class="settings-grid">
    <Panel :title="t('settings.language')"><div class="panel-body stack">
      <label class="field"><span>{{ t('settings.language') }}</span><select :value="current.preferences.locale" class="select" @change="preferences({ locale: ($event.target as HTMLSelectElement).value })"><option v-for="locale in localeList" :key="locale.id" :value="locale.id">{{ locale.name }}</option></select></label>
      <label class="field"><span>{{ t('form.timezone') }}</span><input :value="current.preferences.timeZone" list="time-zone-options" class="input" @change="preferences({ timeZone: ($event.target as HTMLInputElement).value })" /><datalist id="time-zone-options"><option v-for="zone in timeZones" :key="zone" :value="zone" /></datalist></label>
    </div></Panel>
    <Panel :title="t('settings.font')"><div class="panel-body stack"><label class="field"><span>{{ t('settings.font') }}</span><select :value="current.preferences.fontId" class="select" @change="preferences({ fontId: ($event.target as HTMLSelectElement).value })"><option v-for="font in fontList" :key="font.id" :value="font.id">{{ font.id === 'system' ? t('settings.systemFont') : font.name }}</option></select></label></div></Panel>
    <Panel :title="t('settings.theme')" class="settings-full"><div class="panel-body theme-grid"><button v-for="theme in themeList" :key="theme.id" type="button" class="theme-option" :aria-pressed="current.preferences.themeId === theme.id" @click="preferences({ themeId: theme.id })">
      <span class="theme-preview" :style="{ background: theme.palette.background }"><span :style="{ background: theme.palette.surface }" /><span :style="{ background: theme.palette.accent }" /></span><span class="theme-name">{{ theme.name[currentLocale] || theme.name['en-US'] || Object.values(theme.name)[0] }}<Icon v-if="current.preferences.themeId === theme.id" name="check" :size="15" /></span>
    </button></div></Panel>
    <Panel :title="t('settings.categories')"><template #actions><UiButton variant="ghost" icon :aria-label="t('settings.addCategory')" @click="addCategory"><Icon name="plus" :size="18" /></UiButton></template><div v-for="category in current.categories" :key="category.id" class="list-row"><i class="color-dot" :style="{ background: category.color }" /><span class="grow">{{ categoryName(category) }}</span><UiButton variant="ghost" icon :aria-label="t('common.edit') + ': ' + categoryName(category)" @click="editCategory(category.id)"><Icon name="edit" :size="17" /></UiButton></div></Panel>
    <div class="stack"><Panel :title="t('settings.data')"><div class="panel-body"><ArchiveTools /></div></Panel><Panel :title="t('settings.about')"><div class="panel-body stack"><strong>EffiLife</strong><p class="muted small">{{ t('settings.version', { version }) }} · {{ t('app.tagline') }}</p></div></Panel></div>
    <PackageTools />
  </div>
  <UiDialog :open="categoryOpen" :title="form.categoryId ? t('common.edit') : t('settings.addCategory')" @close="categoryOpen = false"><form class="stack" @submit.prevent="saveCategory"><label class="field"><span>{{ t('form.title') }}</span><input v-model="form.name" class="input" required /></label><div class="form-grid"><label class="field"><span>{{ t('form.color') }}</span><input v-model="form.color" type="color" class="input" /></label><label class="field"><span>{{ t('form.difficulty') }}</span><input v-model.number="form.difficulty" type="number" min="0" class="input" required /></label></div><p v-if="error" role="alert" class="form-error">{{ error }}</p><div class="dialog-footer"><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div></form></UiDialog>
</template>

