import { createRouter, createWebHistory } from 'vue-router'

import CaseDetailView from './views/CaseDetailView.vue'
import DashboardView from './views/DashboardView.vue'
import LoginView from './views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: LoginView },
    { path: '/cases', component: DashboardView },
    { path: '/cases/:id', component: CaseDetailView, props: true }
  ]
})

export default router
