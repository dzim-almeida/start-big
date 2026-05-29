import router from '@/router';
import { useAuthStore } from '../stores/auth.store';

export function useAppNavigation() {
  const authStore = useAuthStore();

  const goToLogin = () => router.push({ name: 'auth.user' });

  const goToEnterpriseRegister = () => router.push({ name: 'onboarding' });

  const goToHome = () => router.push({ name: 'home' });

  const logoutAndRedirect = () => {
    authStore.logoutUser();
    router.replace({ name: 'auth.user' });
  };

  return {
    goToLogin,
    goToEnterpriseRegister,
    goToHome,
    logoutAndRedirect,
  };
}
