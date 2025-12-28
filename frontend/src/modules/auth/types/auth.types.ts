/**
 * @fileoverview Tipos TypeScript para o módulo de autenticação
 * @description Define as interfaces e tipos utilizados nas operações de login,
 * cadastro e gerenciamento de sessão do usuário.
 */

/**
 * Payload de requisição para login do usuário
 */
export interface LoginRequest {
  email: string;
  senha: string;
}

/**
 * Resposta da API após login bem-sucedido
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * Payload de requisição para cadastro de novo usuário
 */
export interface RegisterRequest {
  nome: string;
  email: string;
  senha: string;
}

export interface RegisterResponse {
  nome: string,
  email: string,
  id: number,
  empresa_id: number,
  ativo: boolean,
  is_master: boolean
}

/**
 * Tipo para as abas de autenticação
 */
export type AuthTab = 'entrar' | 'cadastrar';
