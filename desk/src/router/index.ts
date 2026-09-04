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
      path: '/records',
      name: 'records',
      component: () => import('@/views/RecordsView.vue'),
    },
    {
      path: '/calendar',
      name: 'calendar',
      component: () => import('@/views/CalendarView.vue'),
    },
    {
      path: '/management',
      name: 'management',
      component: () => import('@/views/ManagementView.vue'),
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
  ],
})

export default router
