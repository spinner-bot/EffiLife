<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { t } from '../../i18n'
import PageHeader from '../../ui/PageHeader.vue'
import Icon from '../../ui/Icon.vue'
const entries = [
  { path: 'categories', title: 'settings.categories', icon: 'tag', help: 'more.categoriesHelp' },
  { path: 'time-plans', title: 'planning.manage', icon: 'calendar', help: 'more.plansHelp' },
  { path: 'rules', title: 'planning.rules', icon: 'repeat', help: 'more.rulesHelp' },
  { path: 'appearance', title: 'more.appearance', icon: 'theme', help: 'more.appearanceHelp' },
  { path: 'settings', title: 'nav.settings', icon: 'settings', help: 'more.settingsHelp' },
]
</script>
<template>
  <PageHeader :title="t('nav.more')" :subtitle="t('more.subtitle')" />
  <section class="panel"><RouterLink v-for="entry in entries" :key="entry.path" :to="'/more/' + entry.path" class="list-row more-entry"><span class="row-mark"><Icon :name="entry.icon" /></span><span class="grow"><strong>{{ t(entry.title) }}</strong><span class="row-detail" style="display: block">{{ t(entry.help) }}</span></span><Icon name="next" :size="18" /></RouterLink></section>
</template>
<style scoped>.more-entry { text-decoration: none; color: var(--ink); padding-block: 1.25rem; transition: background var(--motion-fast); }.more-entry:hover { background: var(--subtle); }</style>
