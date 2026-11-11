<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  type?: 'button' | 'submit' | 'reset'
  icon?: boolean
  wide?: boolean
  disabled?: boolean
}>(), { variant: 'secondary', type: 'button' })
</script>
<template><button :type="type" :disabled="disabled" class="button" :class="[variant, { icon, wide }]"><slot /></button></template>

