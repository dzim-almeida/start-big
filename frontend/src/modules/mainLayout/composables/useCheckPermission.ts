import { useAuthStore } from "@/shared/store/auth.store";

export function useCheckPermission() {
    const { user } = useAuthStore();
    const userPermission = user?.permissoes

    function hasPermission(permission?: string) {
        if (!permission) return true;
        if (userPermission) {
            return userPermission['all'] || userPermission[permission] || false
        }
    }

    return { hasPermission }
}