import { useRouter } from "vue-router";

export function useAppNavigation() {
    const router = useRouter();
    
    const goToLogin = () => router.push({ name: 'auth.user' });
    
    const goToEnterpriseRegister = () => router.push({ name: 'onboarding' });

    const goToHome = () => router.push({ name: 'home' });

    const logoutAndRedirect = () => {
        router.replace({ name: 'auth.user' })
    }

    return {
        goToLogin,
        goToEnterpriseRegister,
        goToHome,
        logoutAndRedirect
    }
}