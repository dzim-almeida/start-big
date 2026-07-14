import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/configuracao-rede',
    name: 'network-config',
    component: () => import('./views/NetworkConfigView.vue'),
    meta: { requiresAuth: false, skipLicenseCheck: true },
  },
  {
    path: '/erro-conexao',
    name: 'erro-conexao',
    component: () => import('./views/ConnectionErrorView.vue'),
    meta: { requiresAuth: false, skipLicenseCheck: true },
  },
]

export default routes
