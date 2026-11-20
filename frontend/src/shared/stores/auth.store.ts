import { computed } from 'vue'
import { defineStore } from 'pinia';

import { useUserQuery } from '../composables/useUser';
import { useQueryClient } from '@tanstack/vue-query';
import { useNotificacoesStore } from './notificacoes.store';
// O token do login é apagado só pelo tokenSessao.service (LIC-04, D-27)
import { apagarToken } from '../services/tokenSessao.service';

export const useAuthStore = defineStore('auth', () => {
  const queryClient = useQueryClient();

  const { data: userData, isLoading, isError, refetch } = useUserQuery();

  const enderecoData = computed(() => userData.value?.empresa?.enderecos[0] || null);

  const isAuthenticated = computed(() => !!userData.value);

  async function revalidateUser() {
    await queryClient.invalidateQueries({ queryKey: ['user-me'] });
    await refetch()
  }

  function logoutUser() {
    apagarToken(); // encerra a sessão desta janela
    queryClient.removeQueries({ queryKey: ['user-me'] });
    useNotificacoesStore().resetar();
  }

  return {
    // refs
    userData,
    enderecoData,

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
