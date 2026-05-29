import { useAuthStore } from '@/shared/stores/auth.store';
import { Permissions } from '@/shared/types/auth.types';
import { PERMISSIONS, PERMISSION_ALIASES } from '@/shared/constants/permissions.constants';
import { storeToRefs } from 'pinia';

export function useCheckPermission() {
  const authStore = useAuthStore();
  const { userData } = storeToRefs(authStore);
  

  function hasPermission(permission?: Permissions) {
    if (!permission) return true;

    const userPermission = userData?.value?.cargo?.permissoes;
    if (!userPermission) return false;

    if (userPermission[PERMISSIONS.all]) return true;
    if (userPermission[permission]) return true;

    const aliases = PERMISSION_ALIASES[permission] || [];
    return aliases.some((alias) => userPermission[alias]);
  }

  return { hasPermission };
}
