/**
 * @fileoverview Configuração centralizada do cliente Axios
 * @description Cria uma instância configurada do Axios com interceptors
 * para autenticação e tratamento de erros.
 */

import axios from 'axios';
import router from '@/router';
import { toast } from 'vue-sonner';

import { useAuthStore } from '@/shared/stores/auth.store';

/**
 * Instância do Axios configurada com a URL base da API
 */
export const api = axios.create({
  // baseURL: "https://attorney-constitutes-attempts-congressional.trycloudflare.com/api/v1",
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  withCredentials: true,
});

/**
 * Interceptor de resposta para tratamento global de erros
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Erro de rede - sem resposta do servidor
    if (!error.response) {
      console.error('[API] Erro de rede:', error.message);
      return Promise.reject(error);
    }

    if (axios.isAxiosError(error)) {
      const { status, data } = error.response;

      // Token expirado ou inválido - limpa autenticação
      if (status === 401) {
        const authStore = useAuthStore();
        if (data.detail === 'Credenciais Inválidas') {
          toast.error(
            'Sessão Expirada',
            {
              description: 'Faça login novamente'
            }
          )
        }
        authStore.logoutUser();
        router.replace({ name: 'auth.user' });
        return Promise.reject(error);
      }

      // Log de erros do servidor para debug
      if (status >= 500) {
        console.error('[API] Erro do servidor:', status, error.response?.data);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
