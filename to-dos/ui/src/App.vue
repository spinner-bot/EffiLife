<script setup lang="ts">
import TodosView from './views/TodosView.vue'
</script>

<template>
  <div class="app-container">
    <TodosView />
  </div>
</template>

<style>
.app-container {
  min-height: 100vh;
  background-color: var(--color-bg);
}
</style>
