/**
 * @fileoverview Troca de servidor: transferir a licença para este computador,
 * consultar a licença desta máquina e desativá-la antes de trocar.
 */

import axios from 'axios';
import api from '@/api/axios';
import { getApiBaseUrl } from '@/api/backendUrl';
import { obterHwid } from '@/shared/services/system/hwid.service';

export interface TransferenciaResultado {
  transferida: boolean;
  /** O banco já tem empresa e master — o caso normal de banco copiado. */
  inicializado: boolean;
}

export interface LicencaEstaMaquina {
  ativada_nesta_maquina: boolean;
  licenca_id: string;
  computador: string;
  limite_computadores: number;
  computadores_conectados: number;
  data_vencimento: string;
  ultima_sincronizacao: string | null;
}

/**
 * Transfere para este computador a licença que veio no banco copiado.
 *
 * Axios puro, sem o interceptor de 401: roda ANTES do login (o banco copiado
 * não deixa ninguém entrar), e um 401 aqui é "senha da conta StartBig errada",
 * não "sessão expirada".
 */
export async function transferirLicenca(email: string, senha: string): Promise<TransferenciaResultado> {
  const { data } = await axios.post<TransferenciaResultado>(
    `${getApiBaseUrl()}/licenca/transferir`,
    { email, senha },
  );
  return data;
}

export async function obterLicencaEstaMaquina(): Promise<LicencaEstaMaquina> {
  const { data } = await api.get<LicencaEstaMaquina>('/licenca/esta-maquina');
  return data;
}

/** Libera a licença deste servidor na nuvem. Só funciona no próprio servidor. */
export async function desativarEstaMaquina(): Promise<void> {
  const hwid = await obterHwid();
  await api.post('/licenca/desativar', { hwid });
}
