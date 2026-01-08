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
        component: () => import('./views/HomeView.vue'),
      },
    ],
  },
];

export default homeRoutes;
