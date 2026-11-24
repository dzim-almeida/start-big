/**
 * @fileoverview Rotas do módulo de sign-in
 * @description Define as rotas para o fluxo de configuração inicial do sistema.
 */

import type { RouteRecordRaw } from 'vue-router';
import { sistemaFoiConfigurado } from '@/shared/services/sistema.service';

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
      // Só manda para o login quando o setup JÁ terminou (existe usuário Master).
      // Ter licença não basta: depois do re-login a licença está salva, mas a
      // empresa e o usuário ainda não existem, e a pessoa precisa voltar aqui
      // para terminar o formulário.
      if ((await sistemaFoiConfigurado()) === true) {
        return { name: 'auth.user' };
      }
      // false (falta o setup) ou null (não deu para perguntar): fica no sign-in,
      // como antes.
    },
  },
];

export default routes;
