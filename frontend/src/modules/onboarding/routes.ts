/**
 * @fileoverview Rotas do módulo de onboarding
 * @description Define as rotas para o fluxo de configuração inicial da empresa.
 */

import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('./views/OnboardingView.vue'),
    meta: {
      title: 'Configuração Inicial - Start Big',
      requiresAuth: true,
    },
  },
];

export default routes;
