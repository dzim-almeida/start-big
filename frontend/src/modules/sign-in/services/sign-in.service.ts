import api from '@/api/axios';
// O token do login é guardado só pelo tokenSessao.service (LIC-04, D-27)
import { guardarToken } from '@/shared/services/tokenSessao.service';
import axios from 'axios';
import { getApiBaseUrl } from '@/api/backendUrl';
import type {
  ReconnectResponse,
  RestaurarBackupResposta,
  SetupRequest,
  ViaCepResponse,
} from '../types/sign-in.types';

/**
 * Executa o setup inicial do sistema (público, sem auth)
 * Usa axios plain para evitar interceptor 401 que redirecionaria para login.
 */
export async function setupSistema(setupData: SetupRequest): Promise<{ access_token: string; token_type: string }> {
  const { data } = await axios.post<{ access_token: string; token_type: string }>(
    `${getApiBaseUrl()}/auth/setup`,
    setupData,
  );
  guardarToken(data.access_token); // o setup já deixa o dono logado nesta janela
  return data;
}

/**
 * Liga a conta StartBig a este computador (re-login).
 * Com o banco sem empresa, a resposta traz também `backup` e `titular` (LIC-03).
 */
export async function reconnectLicenca(email: string, senha: string): Promise<ReconnectResponse> {
  const { data } = await axios.post<ReconnectResponse>(
    `${getApiBaseUrl()}/auth/reconnect`,
    { email, senha }
  );
  return data;
}

/**
 * Prepara a restauração do backup da nuvem depois do re-login (LIC-03 §4.1).
 * A senha da conta vai de novo (D-07): é ela que autoriza trocar o banco.
 * Rota pública, como o re-login: ainda não existe usuário local.
 */
export async function restaurarBackupDaNuvem(
  email: string,
  senha: string,
  ciclo?: string | null,
): Promise<RestaurarBackupResposta> {
  const { data } = await axios.post<RestaurarBackupResposta>(
    `${getApiBaseUrl()}/licenca/restaurar-backup`,
    { email, senha, ciclo: ciclo ?? null },
  );
  return data;
}

/**
 * Pede um novo link de confirmação ou de nova senha para o e-mail (LIC-03 §6.5).
 * O backend responde sempre 202, exista ou não a conta.
 */
export async function reenviarLink(email: string): Promise<void> {
  await axios.post(`${getApiBaseUrl()}/licenca/reenviar-link`, { email });
}

/**
 * Consulta endereço pelo CEP usando a API ViaCEP
 */
export async function getAddressByCep(cep: string): Promise<ViaCepResponse> {
  const { data } = await axios.get(`https://viacep.com.br/ws/${cep}/json/`);
  if (data.erro) {
    throw new Error('CEP não encontrado');
  }
  return data;
}

/**
 * Upload da logo da empresa (requer auth, chamado após setup)
 */
export async function uploadEmpresaLogo(file: File): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);
  await api.post('empresas/imagem', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}
