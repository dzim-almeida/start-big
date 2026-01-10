import type { RouteRecordRaw } from 'vue-router';

const homeRoutes: RouteRecordRaw[] = [
  {
    path: '/home',
    component: () => import('@/modules/mainLayout/views/MainLayout.vue'),
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/modules/home/views/HomeView.vue'),
        meta: {
          title: 'Início',
          subtitle: 'Resumo de vendas e pendencias',
          tabId: 'home'
        }
      },
      {
        path: '/vendas',
        name: 'sales',
        component: () => import('@/modules/home/views/HomeView.vue'),
        meta: {
          title: 'Vendas',
          subtitle: 'Resumo de vendas do sistema',
          tabId: 'sales'
        }
      },
    ],
  },
];

export default homeRoutes;
