import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './features/overview/HomeView.vue'

export const navigation = [
  { path: '/', key: 'nav.home', icon: 'overview' },
  { path: '/plans', key: 'nav.plans', icon: 'plans' },
  { path: '/time', key: 'nav.time', icon: 'time' },
  { path: '/todos', key: 'nav.todos', icon: 'todos' },
  { path: '/settings', key: 'nav.settings', icon: 'settings' },
]
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: { title: 'nav.home' } },
    { path: '/plans', name: 'plans', component: () => import('./features/plans/PlansView.vue'), meta: { title: 'nav.plans' } },
    { path: '/plans/:id', name: 'plan', component: () => import('./features/plans/PlanDetailView.vue'), meta: { title: 'nav.plans' } },
    { path: '/time', name: 'time', component: () => import('./features/time/TimeView.vue'), meta: { title: 'nav.time' } },
    { path: '/todos', name: 'todos', component: () => import('./features/todos/TodosView.vue'), meta: { title: 'nav.todos' } },
    { path: '/settings', name: 'settings', component: () => import('./features/settings/SettingsView.vue'), meta: { title: 'nav.settings' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(to, from, saved) { return saved || (to.path === from.path ? {} : { top: 0 }) },
})

