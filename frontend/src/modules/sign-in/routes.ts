/**
 * @fileoverview Rotas do módulo de sign-in
 * @description Define as rotas para o fluxo de configuração inicial do sistema.
 */

import type { RouteRecordRaw } from 'vue-router';
import { checkSystemStatus } from './services/sign-in.service';

const routes: RouteRecordRaw[] = [
  {
    path: '/sign-in',
    name: 'sign-in',
    component: () => import('./views/SignInView.vue'),
    meta: {
      requiresAuth: false,
    },
    beforeEnter: async () => {
      try {
        const status = await checkSystemStatus();
        if (status.inicializado) {
          return { name: 'auth.user' };
        }
      } catch {
        // Se a API falhar, permite acesso (melhor errar permitindo setup)
      }
    },
  },
];

export default routes;
