/**
 * @fileoverview Configuração centralizada do cliente Axios
 * @description Cria uma instância configurada do Axios com interceptors
 * para autenticação e tratamento de erros.
 */

import axios from 'axios';

/**
 * Instância do Axios configurada com a URL base da API
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Interceptor de requisição para adicionar token de autenticação
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Interceptor de resposta para tratamento global de erros
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Erro de rede - sem resposta do servidor
    if (!error.response) {
      console.error('[API] Erro de rede:', error.message);
      return Promise.reject(error);
    }

    const { status } = error.response;

    // Token expirado ou inválido - limpa autenticação
    if (status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('token_type');
    }

    // Log de erros do servidor para debug
    if (status >= 500) {
      console.error('[API] Erro do servidor:', status, error.response?.data);
    }

    return Promise.reject(error);
  }
);

export default api;
