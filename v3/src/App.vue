<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { navigation } from './router'
import { current, workspace, loading, startupError, initialize, dispatch } from './application/runtime'
import { t, setLocale, currentLocale, errorMessage } from './i18n'
import { defaultHeaderClock } from './domain/preferences'
import { headerClockText } from './ui/header-clock'
import { applyTheme } from './ui/themes'
import { applyFont } from './ui/fonts'
import { openRecord, notify } from './ui/state'
import { useNow } from './ui/useNow'
import Icon from './ui/Icon.vue'
import UiButton from './ui/UiButton.vue'
import EmptyState from './ui/EmptyState.vue'
import FeedbackHost from './ui/FeedbackHost.vue'
import RecordDialog from './features/recording/RecordDialog.vue'
import ArchiveTools from './features/settings/ArchiveTools.vue'
import { reconcileResources } from './extensions/resources'
import { safeMode, enterSafeMode, leaveSafeMode } from './extensions/safe-mode'
import ThemeHost from './ui/ThemeHost.vue'

const route = useRoute()
const version = __APP_VERSION__
const replacementLayout = ref(false)
const requestedReplacement = computed(() => !safeMode && current.value.packages.some(entry => entry.kind === 'theme' && entry.id === current.value.preferences.themeId && entry.status === 'enabled' && entry.grants.includes('app.layout')))
async function recover() {
  try { await dispatch({ type: 'recoverAppearance' }); if (safeMode) leaveSafeMode() }
  catch (error) { notify(errorMessage(error), 'error') }
}
function recoveryKey(event: KeyboardEvent) { if (event.altKey && event.shiftKey && event.code === 'Digit0') { event.preventDefault(); enterSafeMode() } }
function skipContent() { const main = document.getElementById('main-content'); main?.focus(); main?.scrollIntoView({ block: 'start' }) }
const colorScheme = matchMedia('(prefers-color-scheme: dark)')
function schemeChanged() { applyTheme(safeMode ? 1 : current.value.preferences.themeId) }
const title = computed(() => t(String(route.meta.title || 'nav.home')))
const now = useNow()
const clockOptions = computed(() => current.value.preferences.headerClock || defaultHeaderClock)
const today = computed(() => headerClockText(now.value, currentLocale.value, current.value.preferences.timeZone, clockOptions.value))
watch(() => [current.value.preferences, current.value.packages] as const, async ([preferences, packages]) => {
  reconcileResources(safeMode ? [] : packages, version)
  setLocale(safeMode ? 'zh-CN' : preferences.locale)
  applyTheme(safeMode ? 1 : preferences.themeId)
  try { await applyFont(safeMode ? 'default' : preferences.fontId) } catch (error) { notify(errorMessage(error), 'error') }
}, { immediate: true })
watch(title, value => { document.title = value + ' · EffiLife' }, { immediate: true })
onMounted(() => {
  initialize()
  window.addEventListener('keydown', recoveryKey)
  colorScheme.addEventListener('change', schemeChanged)
})
onBeforeUnmount(() => { window.removeEventListener('keydown', recoveryKey); colorScheme.removeEventListener('change', schemeChanged) })
</script>
<template>
  <a href="#main-content" class="skip-link" @click.prevent="skipContent">{{ t('common.skipContent') }}</a>
  <div v-if="loading" style="min-height: 100dvh; display: grid; place-items: center"><p role="status">{{ t('common.loading') }}</p></div>
  <div v-else-if="startupError && !workspace" class="app-main stack" style="max-width: 800px">
    <EmptyState :title="t('state.startupFailed')" :description="t('state.startupBody')" icon="error"><UiButton variant="primary" @click="initialize">{{ t('common.retry') }}</UiButton></EmptyState>
    <p role="alert" class="form-error">{{ errorMessage(startupError) }}</p><ArchiveTools recovery />
  </div>
  <div v-else v-show="!replacementLayout" class="app-shell">
    <aside class="app-sidebar" :aria-label="t('common.navigation')">
      <div class="sidebar-brand"><RouterLink to="/" class="brand"><span class="brand-mark"><Icon name="activity" :size="23" /></span>EffiLife</RouterLink><p class="brand-tagline">{{ t('app.tagline') }}</p></div>
      <nav class="nav-list" :aria-label="t('common.navigation')"><RouterLink v-for="item in navigation" :key="item.path" :to="item.path" class="nav-item" :class="{ 'router-link-active': (item.path === '/plans' && route.path.startsWith('/plans/')) || (item.path === '/more' && route.path.startsWith('/more/')) }" :exact-active-class="item.path === '/' ? 'router-link-active' : undefined"><Icon :name="item.icon" :size="20" /><span>{{ t(item.key) }}</span></RouterLink></nav>
      <div class="sidebar-bottom"><p class="sidebar-version">EffiLife v{{ version }}</p></div>
    </aside>
    <div class="app-body">
      <header class="app-topbar" :data-clock-align="clockOptions.align"><span class="breadcrumb">EffiLife <span aria-hidden="true">/</span> {{ title }}</span><RouterLink to="/" class="mobile-brand">EffiLife</RouterLink><time class="muted small topbar-date" :datetime="now" :data-display="clockOptions.display">{{ today }}</time><div class="topbar-actions"><UiButton variant="primary" @click="openRecord()"><Icon name="plus" :size="18" />{{ t('common.record') }}</UiButton></div></header>
      <main id="main-content" class="app-main" tabindex="-1"><p v-if="startupError" role="alert" class="form-error">{{ errorMessage(startupError) }}</p><RouterView /></main>
    </div>
  </div>
  <ThemeHost v-if="!loading && workspace" @layout="value => replacementLayout = value" />
  <div v-if="safeMode || requestedReplacement" class="recovery-dock"><span v-if="safeMode">{{ t('extensions.safeMode') }}</span><UiButton @click="recover">{{ t('extensions.recover') }}</UiButton></div>
  <RecordDialog /><FeedbackHost />
</template>

