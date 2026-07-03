import router from '@/router';
import { useAuthStore } from '../stores/auth.store';
import { logout } from '@/modules/auth/services/auth.service';
import { desconectarLicenca } from '@/shared/services/licenca.service';

export function useAppNavigation() {
  const authStore = useAuthStore();

  const goToLogin = () => router.push({ name: 'auth.user' });

  const goToSignIn = () => router.push({ name: 'sign-in' });

  const goToHome = () => router.push({ name: 'home' });

  const goToMinhaConta = () => router.push({ name: 'minha-conta' });

  const logoutAndRedirect = async () => {
    await desconectarLicenca();
    try {
      await logout();
    } catch {
      // Mesmo se a API falhar, limpa o estado local
    }
    authStore.logoutUser();
    router.replace({ name: 'auth.user' });
  };

  return {
    goToLogin,
    goToSignIn,
    goToHome,
    goToMinhaConta,
    logoutAndRedirect,
  };
}
