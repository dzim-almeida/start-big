import { useAuthStore } from '@/shared/stores/auth.store';
import { Permissions } from '@/shared/types/auth.types';
import { storeToRefs } from 'pinia';

export function useCheckPermission() {
  const authStore = useAuthStore();
  const { userData } = storeToRefs(authStore);
  

  function hasPermission(permission?: Permissions) {
    if (!permission) return true;

    const userPermission = userData?.value?.cargo?.permissoes;

    if (userPermission) {
      return userPermission['all'] || userPermission[permission] || false;
    }
  }

  return { hasPermission };
}
