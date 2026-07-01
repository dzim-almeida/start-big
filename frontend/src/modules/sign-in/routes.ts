/**
 * @fileoverview Rotas do módulo de sign-in
 * @description Define as rotas para o fluxo de configuração inicial do sistema.
 */

import type { RouteRecordRaw } from 'vue-router';
import { verificarLicenca } from '@/shared/services/licenca.service';

const routes: RouteRecordRaw[] = [
  {
    path: '/sign-in',
    name: 'sign-in',
    component: () => import('./views/SignInView.vue'),
    meta: {
      requiresAuth: false,
      skipLicenseCheck: true,
    },
    beforeEnter: async () => {
      try {
        await verificarLicenca();
        // Licença válida = sistema já inicializado → redirecionar para login
        return { name: 'auth.user' };
      } catch {
        // 404/403/erro de rede → sistema não inicializado → permitir setup
      }
    },
  },
];

export default routes;
