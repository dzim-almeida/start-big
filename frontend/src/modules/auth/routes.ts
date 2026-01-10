import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'auth.user',
    component: () => import('./views/LoginView.vue'),
  },
];

export default routes;
