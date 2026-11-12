import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './features/overview/HomeView.vue'

export const navigation = [
  { path: '/', key: 'nav.home', icon: 'overview' },
  { path: '/plans', key: 'nav.plans', icon: 'plans' },
  { path: '/time', key: 'nav.time', icon: 'time' },
  { path: '/todos', key: 'nav.todos', icon: 'todos' },
  { path: '/more', key: 'nav.more', icon: 'more' },
]
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: { title: 'nav.home' } },
    { path: '/plans', name: 'plans', component: () => import('./features/plans/PlansView.vue'), meta: { title: 'nav.plans' } },
    { path: '/plans/:id', name: 'plan', component: () => import('./features/plans/PlanDetailView.vue'), meta: { title: 'nav.plans' } },
    { path: '/time', name: 'time', component: () => import('./features/time/TimeView.vue'), meta: { title: 'nav.time' } },
    { path: '/time/records/:id', name: 'record', component: () => import('./features/time/RecordDetailView.vue'), meta: { title: 'time.records' } },
    { path: '/todos', name: 'todos', component: () => import('./features/todos/TodosView.vue'), meta: { title: 'nav.todos' } },
    { path: '/more', component: () => import('./features/settings/MoreView.vue'), meta: { title: 'nav.more' } },
    { path: '/more/categories', component: () => import('./features/categories/CategoriesView.vue'), meta: { title: 'settings.categories' } },
    { path: '/more/time-plans', component: () => import('./features/time/TimePlansView.vue'), meta: { title: 'planning.manage' } },
    { path: '/more/rules', component: () => import('./features/time/TimeRulesView.vue'), meta: { title: 'planning.rules' } },
    { path: '/more/appearance', component: () => import('./features/settings/AppearanceView.vue'), meta: { title: 'more.appearance' } },
    { path: '/more/settings', name: 'settings', component: () => import('./features/settings/SettingsView.vue'), meta: { title: 'settings.title' } },
    { path: '/settings', redirect: '/more/settings' },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(to, from, saved) { return saved || (to.path === from.path ? {} : { top: 0 }) },
})

