import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'login.user',
    component: () => import('./views/LoginView.vue'),
  },
  {
    path: '/verify-email',
    name: 'verify.email',
    component: () => import('./views/VerifyEmailView.vue'),
  },
];

export default routes;
