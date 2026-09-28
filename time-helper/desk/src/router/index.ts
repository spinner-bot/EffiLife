import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/plans',
      name: 'plansHub',
      component: () => import('@/views/PlansHubView.vue'),
    },
    {
      path: '/plan',
      name: 'plan',
      redirect: { path: '/plans', query: { mode: 'time' } },
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: () => import('@/views/TaskCenterView.vue'),
    },
    {
      path: '/records',
      name: 'records',
      component: () => import('@/views/RecordsView.vue'),
    },
    // Keep old bookmarks usable after removing the standalone calendar entry.
    {
      path: '/calendar',
      redirect: '/records',
    },
    // Keep legacy management bookmarks inside the unified plan workspace.
    {
      path: '/management',
      name: 'management',
      redirect: { path: '/plans', query: { mode: 'time' } },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
    },
    {
      path: '/day/:date',
      name: 'dayDetail',
      component: () => import('@/views/DayDetailView.vue'),
    },
    {
      path: '/audio-settings',
      name: 'audioSettings',
      component: () => import('@/views/AudioSettingsView.vue'),
    },
    {
      path: '/event-manager',
      name: 'eventManager',
      component: () => import('@/views/EventManagerView.vue'),
    },
    {
      path: '/motion-settings',
      name: 'motionSettings',
      component: () => import('@/views/MotionSettingsView.vue'),
    },
    {
      path: '/checkin',
      name: 'checkin',
      component: () => import('@/views/CheckinView.vue'),
    },
  ],
})

export default router
