import api from '@/api/axios';
import type { UserResponse } from '@/shared/types/auth.types';

export interface AtualizarContaPayload {
  nome?: string;
  email?: string;
}

export interface AlterarSenhaPayload {
  senha_atual: string;
  nova_senha: string;
}

export async function atualizarConta(dados: AtualizarContaPayload): Promise<UserResponse> {
  const { data } = await api.patch<UserResponse>('usuarios/me', dados);
  return data;
}

export async function alterarSenha(dados: AlterarSenhaPayload): Promise<UserResponse> {
  const { data } = await api.patch<UserResponse>('usuarios/me/senha', dados);
  return data;
}

export async function uploadFotoPerfil(file: File): Promise<UserResponse> {
  const formData = new FormData();
  formData.append('img_file', file);
  const { data } = await api.post<UserResponse>('usuarios/imagem', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
