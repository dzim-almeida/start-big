/**
 * @fileoverview Serviço de verificação de licença.
 * Usa axios puro (sem interceptor 401) pois executa antes da autenticação.
 */

import axios from 'axios';
import { getApiBaseUrl } from '@/api/backendUrl';

export interface LicencaStatusResponse {
  status: 'online_valid' | 'offline_valid';
  dias_restantes?: number;
}

export interface LicencaErroResponse {
  codigo: string;
  mensagem: string;
}

/**
 * Verifica o status da licença via GET /licenca/status.
 * Endpoint público (sem autenticação).
 */
export async function verificarLicenca(): Promise<LicencaStatusResponse> {
  const { data } = await axios.get<LicencaStatusResponse>(
    `${getApiBaseUrl()}/licenca/status`,
  );
  return data;
}

/**
 * Desconecta a sessão da licença na API StartBig.
 * Chamado no logout e no encerramento da aplicação.
 * Nunca propaga erro — falhas são silenciosas.
 */
export async function desconectarLicenca(): Promise<void> {
  try {
    await axios.post(
      `${getApiBaseUrl()}/licenca/desconectar`,
      null,
      { signal: AbortSignal.timeout(2000) },
    );
  } catch {
    // Silencioso — não bloqueia o fluxo de encerramento
  }
}

/**
 * Retorna a URL completa do endpoint de desconexão.
 * Usada pelo sendBeacon no beforeunload (fecho de janela).
 */
export function getDesconectarUrl(): string {
  return `${getApiBaseUrl()}/licenca/desconectar`;
}
