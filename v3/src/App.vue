<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { navigation } from './router'
import { current, workspace, loading, startupError, initialize } from './application/runtime'
import { t, setLocale, calendarDate, errorMessage } from './i18n'
import { dateKey } from './domain/time'
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

const route = useRoute()
const version = __APP_VERSION__
const title = computed(() => t(String(route.meta.title || 'nav.home')))
const now = useNow()
const today = computed(() => calendarDate(dateKey(now.value, current.value.preferences.timeZone), { weekday: 'long' }))
watch(() => current.value.preferences, async preferences => {
  setLocale(preferences.locale)
  applyTheme(preferences.themeId)
  try { await applyFont(preferences.fontId) } catch (error) { notify(errorMessage(error), 'error') }
}, { immediate: true })
watch(title, value => { document.title = value + ' · EffiLife' }, { immediate: true })
onMounted(() => {
  initialize()
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => applyTheme(current.value.preferences.themeId))
})
</script>
<template>
  <a href="#main-content" class="skip-link">{{ t('common.skipContent') }}</a>
  <div v-if="loading" style="min-height: 100dvh; display: grid; place-items: center"><p role="status">{{ t('common.loading') }}</p></div>
  <div v-else-if="startupError && !workspace" class="app-main stack" style="max-width: 800px">
    <EmptyState :title="t('state.startupFailed')" :description="t('state.startupBody')" icon="error"><UiButton variant="primary" @click="initialize">{{ t('common.retry') }}</UiButton></EmptyState>
    <p role="alert" class="form-error">{{ errorMessage(startupError) }}</p><ArchiveTools recovery />
  </div>
  <div v-else class="app-shell">
    <aside class="app-sidebar" :aria-label="t('common.navigation')">
      <div class="sidebar-brand"><RouterLink to="/" class="brand"><span class="brand-mark"><Icon name="activity" :size="23" /></span>EffiLife</RouterLink><p class="brand-tagline">{{ t('app.tagline') }}</p></div>
      <nav class="nav-list" :aria-label="t('common.navigation')"><RouterLink v-for="item in navigation" :key="item.path" :to="item.path" class="nav-item" :class="{ 'router-link-active': item.path === '/plans' && route.path.startsWith('/plans/') }" :exact-active-class="item.path === '/' ? 'router-link-active' : undefined"><Icon :name="item.icon" :size="20" /><span>{{ t(item.key) }}</span></RouterLink></nav>
      <div class="sidebar-bottom"><p class="sidebar-version">EffiLife v{{ version }}</p></div>
    </aside>
    <div class="app-body">
      <header class="app-topbar"><span class="breadcrumb">EffiLife <span aria-hidden="true">/</span> {{ title }}</span><RouterLink to="/" class="mobile-brand">EffiLife</RouterLink><div class="topbar-actions"><span class="muted small topbar-date">{{ today }}</span><UiButton variant="primary" @click="openRecord()"><Icon name="plus" :size="18" />{{ t('common.record') }}</UiButton></div></header>
      <main id="main-content" class="app-main" tabindex="-1"><p v-if="startupError" role="alert" class="form-error">{{ errorMessage(startupError) }}</p><RouterView /></main>
    </div>
  </div>
  <RecordDialog /><FeedbackHost />
</template>

