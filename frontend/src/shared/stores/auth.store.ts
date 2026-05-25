import { computed } from 'vue'
import { defineStore } from 'pinia';

import { useUserQuery } from '../composables/useUser';
import { useQueryClient } from '@tanstack/vue-query';

export const useAuthStore = defineStore('auth', () => {
  const queryClient = useQueryClient();

  const { data: userData, isLoading, isError, refetch } = useUserQuery();

  const isAuthenticated = computed(() => !!userData.value);

  async function revalidateUser() {
    await queryClient.invalidateQueries({ queryKey: ['user-me'] });
    await refetch()
  }

  function logoutUser() {
    queryClient.removeQueries({ queryKey: ['user-me'] });
  }

  return {
    // refs
    userData,

    // computed
    isAuthenticated,

    // estados
    isLoading,
    isError,

    // metodos
    revalidateUser,
    logoutUser,
  }
});
