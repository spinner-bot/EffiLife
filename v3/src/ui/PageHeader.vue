<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { t } from '../i18n'
import Icon from './Icon.vue'
defineProps<{ title: string; subtitle?: string; eyebrow?: string; back?: string }>()
</script>
<template>
  <header class="page-header">
    <div>
      <RouterLink v-if="back" :to="back" class="back-link"><Icon name="back" :size="17" />{{ t('common.back') }}</RouterLink>
      <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p><h1>{{ title }}</h1><p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.default" class="cluster"><slot /></div>
  </header>
</template>
<style scoped>
.back-link { display: inline-flex; align-items: center; gap: .3rem; margin-block-end: .45rem; color: var(--muted); font-size: .82rem; font-weight: 550; text-decoration: none; border-radius: .4rem; padding: .15rem .4rem; margin-inline-start: -.4rem; transition: background var(--motion-fast), color var(--motion-fast); }
.back-link:hover, .back-link:focus-visible { background: var(--subtle); color: var(--ink); }
</style>
