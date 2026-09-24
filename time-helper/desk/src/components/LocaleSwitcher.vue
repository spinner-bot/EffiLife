<script setup lang="ts">
import { useI18n } from '@/i18n'

const { locale, setLocale, t, localeOptions } = useI18n()
</script>

<template>
  <label class="locale-switcher">
    <span>{{ t('locale.label') }}</span>
    <select v-model="locale" @change="setLocale(locale)">
      <option v-for="option in localeOptions" :key="option" :value="option">{{ t(`locale.${option}`) }}</option>
    </select>
  </label>
</template>

<style scoped>
.locale-switcher { display: inline-flex; align-items: center; gap: 8px; color: var(--color-text-secondary); font-size: 13px; }
.locale-switcher select { border: 1px solid var(--color-border); border-radius: 8px; padding: 6px 8px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.locale-switcher select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
</style>
