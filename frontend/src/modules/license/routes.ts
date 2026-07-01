import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/licenca-erro',
    name: 'licenca.erro',
    component: () => import('./views/LicenseErrorView.vue'),
    meta: {
      skipLicenseCheck: true,
    },
    props: (route) => ({
      codigo: (route.query.codigo as string) || '',
      mensagem: (route.query.mensagem as string) || '',
    }),
  },
];

export default routes;
