import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/configuracao-rede',
    name: 'network-config',
    component: () => import('./views/NetworkConfigView.vue'),
    meta: { requiresAuth: false },
  },
]

export default routes
