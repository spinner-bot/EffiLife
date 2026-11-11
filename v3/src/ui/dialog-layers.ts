import { computed, onBeforeUnmount, shallowRef, watch } from 'vue'

const stack = shallowRef<symbol[]>([])
/** Teleport source order can differ from open order after a route is lazy-loaded. */
export function useDialogLayer(open: () => boolean) {
  const token = Symbol('dialog')
  const remove = () => { stack.value = stack.value.filter(entry => entry !== token) }
  watch(open, value => { remove(); if (value) stack.value = [...stack.value, token] }, { immediate: true, flush: 'sync' })
  onBeforeUnmount(remove)
  const depth = computed(() => Math.max(0, stack.value.indexOf(token)) * 2)
  return {
    overlay: computed(() => ({ zIndex: 'calc(var(--layer-modal) + ' + depth.value + ')' })),
    content: computed(() => ({ zIndex: 'calc(var(--layer-modal) + ' + (depth.value + 1) + ')' })),
  }
}

