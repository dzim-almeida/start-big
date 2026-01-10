// import { useAuthStore } from '@/shared/store/auth.store';
import { useLayoutStore } from '@/modules/mainLayout/store/layout.store';
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const modules = import.meta.glob('@/modules/**/routes.ts', { eager: true });

const moduleRoutes: RouteRecordRaw[] = Object.values(modules).flatMap((module: any) => {
  return module.default;
});

const routes: RouteRecordRaw[] = [...moduleRoutes];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// router.beforeEach((to) => {
//   const authStore = useAuthStore();

//   if (to.meta.requiresAuth && !authStore.isAuthenticated) {
//     return {
//       path: '/',
//       query: { redirect: to.fullPath }
//     }
//   }
// });

router.afterEach((to) => {
  const layoutStore = useLayoutStore();
  layoutStore.updatePageInfo(to);
});

export default router;
