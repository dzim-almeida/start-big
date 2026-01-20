import type { RouteRecordRaw } from 'vue-router';

const homeRoutes: RouteRecordRaw[] = [
  {
    path: '/',
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
          tabId: 'home',
          requiresAuth: true
        }
      },
      {
        path: '/vendas',
        name: 'sales',
        component: () => import('@/modules/home/views/HomeView.vue'),
        meta: {
          title: 'Vendas',
          subtitle: 'Resumo de vendas do sistema',
          tabId: 'sales',
          requiresAuth: true
        }
      },
      {
        path: '/equipes',
        name: 'employees',
        component: () => import('@/modules/employees/views/EmployeesView.vue'),
        meta: {
          title: 'Gestão de Equipe',
          subtitle: 'Gerencie os colaboradores da sua organização de forma centralizada.',
          tabId: 'employees',
          requiresAuth: true
        }
      }
    ],
  },
];

export default homeRoutes;
