/**
 * @fileoverview Tipos TypeScript para o módulo de autenticação
 * @description Define as interfaces e tipos utilizados nas operações de login,
 * cadastro e gerenciamento de sessão do usuário.
 */

import { User } from "@/shared/types/auth.types";

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
export interface LoginResponse extends User {}

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

/**
 * Payload de requisição para verificação de e-mail
 */
export interface VerifyEmailRequest {
  email: string;
  code: string;
}

/**
 * Resposta da API após verificação de e-mail
 */
export interface VerifyEmailResponse {
  message: string;
  verified: boolean;
}

/**
 * Payload de requisição para reenvio de código
 */
export interface ResendCodeRequest {
  email: string;
}

/**
 * Resposta da API após reenvio de código
 */
export interface ResendCodeResponse {
  message: string;
}
