<script setup lang="ts">
defineProps<{ title?: string; subtitle?: string }>()
</script>
<template>
  <section class="panel">
    <header v-if="title || $slots.header" class="panel-header">
      <div><slot name="header"><h2>{{ title }}</h2><p v-if="subtitle" class="muted small" style="margin-top: 6px">{{ subtitle }}</p></slot></div>
      <slot name="actions" />
    </header>
    <slot />
  </section>
</template>

