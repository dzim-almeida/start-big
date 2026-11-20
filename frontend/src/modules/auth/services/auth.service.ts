/**
 * @fileoverview Serviço de autenticação
 * @description Contém as funções para comunicação com os endpoints de
 * autenticação da API (login, logout, etc.).
 */

import api from '@/api/axios';
// O token do login é guardado e apagado só pelo tokenSessao.service (LIC-04, D-27)
import { apagarToken, guardarToken } from '@/shared/services/tokenSessao.service';
import { obterHwid } from '@/shared/services/system/hwid.service';

import type {
  LoginRequest,
  LoginResponse,
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
export async function login(credentials: Omit<LoginRequest, 'hwid'>): Promise<LoginResponse> {
    const hwid = await obterHwid();
    const response = await api.post<LoginResponse>('auth/login', {
      ...credentials,
      hwid,
    });
    guardarToken(response.data.access_token); // fica só na sessão desta janela (ADR-003)
    return response.data;
}

/**
 * Realiza o logout do usuário (revoga token no backend)
 */
export async function logout(): Promise<void> {
    try {
        const hwid = await obterHwid();
        await api.post('auth/logout', { hwid });
    } finally {
        apagarToken(); // logout: a sessão acaba mesmo se a chamada ao backend falhar
    }
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
