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
 * Chave utilizadas para armazenamento local
 */
const REMEMBER_ME = 'rememberMe';


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
 * Salva a preferência de "lembrar-me" do usuário
 * @param email - Email a ser lembrado
 */
export function saveRememberMe(email: string): void {
  localStorage.setItem(REMEMBER_ME, email);
}

/**
 * Recupera o email salvo na opção "lembrar-me"
 * @returns Email salvo ou null
 */
export function getRememberedEmail(): string | null {
  return localStorage.getItem(REMEMBER_ME);
}

/**
 * Remove a preferência de "lembrar-me"
 */
export function clearRememberMe(): void {
  localStorage.removeItem(REMEMBER_ME);
}
