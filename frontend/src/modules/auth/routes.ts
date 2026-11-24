import type { RouteRecordRaw } from 'vue-router';
import { sistemaFoiConfigurado } from '@/shared/services/sistema.service';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'auth.user',
    component: () => import('./views/LoginView.vue'),
    meta: {},
    beforeEnter: async () => {
      // Sem o setup feito não existe usuário para entrar: o login seria uma
      // tela sem saída. Volta para o sign-in terminar a configuração.
      if ((await sistemaFoiConfigurado()) === false) {
        return { name: 'sign-in' };
      }
      // true (setup feito) ou null (não deu para perguntar): mostra o login.
    },
  },
];

export default routes;
