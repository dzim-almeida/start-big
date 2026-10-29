import api from '@/api/axios';
import { BASE_ORDER_SERVICE_URL } from '../constants/core.constant';
import type { OsNotaFiscalUpdate, OsNotaFiscalRead } from '../types/notaFiscal.type';
import type { ResultadoVerificacaoFiscal } from '@/shared/types/fiscal.types';

export async function getOsNotaFiscal(osNumero: string): Promise<OsNotaFiscalRead | null> {
  try {
    const { data } = await api.get<OsNotaFiscalRead>(
      `${BASE_ORDER_SERVICE_URL}/${osNumero}/fiscal`,
    );
    return data;
  } catch (err: any) {
    if (err?.response?.status === 404) return null;
    throw err;
  }
}

export async function upsertOsNotaFiscal(
  osNumero: string,
  dados: OsNotaFiscalUpdate,
): Promise<OsNotaFiscalRead> {
  const { data } = await api.put<OsNotaFiscalRead>(
    `${BASE_ORDER_SERVICE_URL}/${osNumero}/fiscal`,
    dados,
  );
  return data;
}

export async function verificarFiscalOS(
  osNumero: string,
  tipoDocumento: string = 'ambos',
): Promise<ResultadoVerificacaoFiscal> {
  const { data } = await api.get<ResultadoVerificacaoFiscal>(
    `${BASE_ORDER_SERVICE_URL}/${osNumero}/verificar-fiscal`,
    { params: { tipo_documento: tipoDocumento } },
  );
  return data;
}

export async function emitirFiscalOS(
  osNumero: string,
  tipoDocumento: string = 'ambos',
): Promise<void> {
  await api.post(
    `${BASE_ORDER_SERVICE_URL}/${osNumero}/emitir-fiscal`,
    null,
    { params: { tipo_documento: tipoDocumento } },
  );
}

/** Um documento fiscal da OS, resumido para o cartão "Notas desta OS". */
export interface NotaDaOs {
  id: number;
  status: string;
  numero: number | string | null;
  motivo: string | null;
  url_pdf: string | null;
  valor: number | null;
  papel: string | null;
}

/** "Notas desta OS" (M5 de docs/nfse-melhorias-plano.md). Valores em centavos. */
export interface NotasDaOs {
  numero_os: string;
  finalizada: boolean;
  total_os: number;
  pecas: { tem: boolean; valor: number; modulo: boolean; documento: NotaDaOs | null };
  servico: { tem: boolean; valor: number; modulo: boolean; documentos: NotaDaOs[] };
}

export async function getNotasDaOs(osNumero: string): Promise<NotasDaOs> {
  const { data } = await api.get<NotasDaOs>(`${BASE_ORDER_SERVICE_URL}/${osNumero}/notas-fiscais`);
  return data;
}
