/**
 * @fileoverview Configuração centralizada do cliente Axios
 * @description Cria uma instância configurada do Axios com interceptors
 * para autenticação e tratamento de erros.
 */

import axios from 'axios';
import router from '@/router';
import { toast } from 'vue-sonner';

import { useAuthStore } from '@/shared/stores/auth.store';
import { getApiBaseUrl } from '@/api/backendUrl';

export const TOKEN_KEY = 'access_token';

/**
 * Instância do Axios configurada com a URL base da API
 */
export const api = axios.create({ timeout: 10_000 });

/**
 * Interceptor de requisição para definir baseURL dinâmica e anexar o JWT Bearer Token
 */
api.interceptors.request.use((config) => {
  config.baseURL ??= getApiBaseUrl();
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
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
      const { status } = error.response;

      // Licença bloqueada remotamente — redireciona para tela de erro
      if (status === 403) {
        const detail = error.response?.data?.detail;
        if (detail?.codigo === 'LICENCA_BLOQUEADA') {
          router.replace({
            name: 'licenca.erro',
            query: { codigo: detail.codigo, mensagem: detail.mensagem },
          });
          return Promise.reject(error);
        }
      }

      // Token expirado ou inválido - limpa autenticação
      if (status === 401) {
        const hadToken = !!localStorage.getItem(TOKEN_KEY);
        const authStore = useAuthStore();

        authStore.logoutUser();

        // Só mostra toast se havia sessão ativa (token expirou de verdade)
        if (hadToken) {
          toast.error(
            'Sessão Expirada',
            {
              description: 'Faça login novamente'
            }
          )
        }

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
