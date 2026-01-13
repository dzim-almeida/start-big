// import { useAuthStore } from '@/shared/store/auth.store';
import { useLayoutStore } from '@/modules/mainLayout/store/layout.store';
import { useAuthStore } from '@/shared/stores/auth.store';
import { storeToRefs } from 'pinia';
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { watch } from 'vue';

const modules = import.meta.glob('@/modules/**/routes.ts', { eager: true });

const moduleRoutes: RouteRecordRaw[] = Object.values(modules).flatMap((module: any) => {
  return module.default;
});

const routes: RouteRecordRaw[] = [...moduleRoutes];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  const { isAuthenticated, isLoading } = storeToRefs(authStore);

  // 1. Se a rota precisa de autenticação
  if (to.meta.requiresAuth) {
    
    // 2. Se a store ainda está carregando, PAUSA o router
    if (isLoading.value) {
      await new Promise<void>((resolve) => {
        // Observa a variável isLoading. Quando virar false, resolve a promessa.
        const unwatch = watch(isLoading, (loading) => {
          if (!loading) {
            unwatch(); // Para de observar para evitar memory leaks
            resolve();
          }
        });
      });
    }

    // 3. Agora que o carregamento terminou (ou nem começou), verifica se logou
    if (!isAuthenticated.value) {
      return ({
        name: 'auth.user',
        query: { redirect: to.fullPath },
      });
    }
  }

});

router.afterEach((to) => {
  const layoutStore = useLayoutStore();
  layoutStore.updatePageInfo(to);
});

export default router;
