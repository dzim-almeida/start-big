/**
 * ===========================================================================
 * ARQUIVO: routes.ts
 * MODULO: Ordem de Servico
 * DESCRICAO: Configuracao de rotas do modulo de Ordem de Servico.
 *            Define a rota principal /ordens-servico com autenticacao.
 * ===========================================================================
 *
 * ROTAS:
 * - /ordens-servico: Pagina principal do modulo (requer autenticacao)
 *   - Renderiza OrdemServicoView dentro do MainLayout
 *   - Inclui tabs: Ordens, Orcamentos, Servicos
 * ===========================================================================
 */
import type { RouteRecordRaw } from 'vue-router';

const ordemServicoRoutes: RouteRecordRaw[] = [
  {
    path: '/ordens-servico',
    component: () => import('@/modules/mainLayout/views/MainLayout.vue'),
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        name: 'ordens-servico',
        component: () => import('./views/OrdemServicoView.vue'),
      },
    ],
  },
];

export default ordemServicoRoutes;
