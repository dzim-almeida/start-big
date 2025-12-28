/**
 * @fileoverview Serviço de autenticação
 * @description Contém as funções para comunicação com os endpoints de
 * autenticação da API (login, logout, etc.).
 */

import api from '@/shared/libs/axios';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
} from '../types/auth.types';

/**
 * Chaves utilizadas para armazenamento local
 */
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  TOKEN_TYPE: 'token_type',
  REMEMBER_ME: 'remember_me',
} as const;

/**
 * Realiza o login do usuário
 * @param credentials - Credenciais de login (email e senha)
 * @returns Promise com os dados de resposta do login
 */
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('auth/login', credentials);
  return response.data;
}

/**
 * Realiza o cadastro do usuário
 * @param data - Dados de cadastro (nome, email, senha)
 * @returns Promise com os dados de resposta do casdatro
 */
export async function register(registerData: RegisterRequest): Promise<RegisterResponse> {
  const response = await api.post<RegisterResponse>('usuarios/', registerData);
  return response.data;
}

/**
 * Armazena o token de acesso no localStorage
 * @param token - Token JWT retornado pela API
 * @param tokenType - Tipo do token (geralmente "bearer")
 */
export function saveToken(token: string, tokenType: string): void {
  localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
  localStorage.setItem(STORAGE_KEYS.TOKEN_TYPE, tokenType);
}

/**
 * Recupera o token de acesso armazenado
 * @returns Token de acesso ou null se não existir
 */
export function getToken(): string | null {
  return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Remove os dados de autenticação do localStorage
 */
export function clearAuth(): void {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.TOKEN_TYPE);
}

/**
 * Verifica se o usuário está autenticado
 * @returns true se houver um token armazenado
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * Salva a preferência de "lembrar-me" do usuário
 * @param email - Email a ser lembrado
 */
export function saveRememberMe(email: string): void {
  localStorage.setItem(STORAGE_KEYS.REMEMBER_ME, email);
}

/**
 * Recupera o email salvo na opção "lembrar-me"
 * @returns Email salvo ou null
 */
export function getRememberedEmail(): string | null {
  return localStorage.getItem(STORAGE_KEYS.REMEMBER_ME);
}

/**
 * Remove a preferência de "lembrar-me"
 */
export function clearRememberMe(): void {
  localStorage.removeItem(STORAGE_KEYS.REMEMBER_ME);
}
