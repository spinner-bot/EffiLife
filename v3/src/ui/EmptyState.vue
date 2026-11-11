<script setup lang="ts">
import Icon from './Icon.vue'
withDefaults(defineProps<{ title: string; description?: string; icon?: string }>(), { icon: 'activity' })
</script>
<template><div class="empty"><div class="empty-icon"><Icon :name="icon" :size="26" /></div><h3>{{ title }}</h3><p v-if="description">{{ description }}</p><slot /></div></template>

