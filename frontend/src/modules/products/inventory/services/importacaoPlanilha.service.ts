/**
 * @fileoverview Importação de produtos por planilha Excel.
 */

import api from '@/api/axios';
import type { PreviaImportacao, ResultadoImportacaoPlanilha } from '../types/importacaoPlanilha.types';

const BASE_URL = 'estoque/importar-planilha' as const;
// Centenas de produtos na mesma transação: o limite padrão de 10 s não basta.
const TEMPO_LIMITE_MS = 180_000;

function formulario(arquivo: File): FormData {
  const form = new FormData();
  form.append('arquivo', arquivo);
  return form;
}

/** Confere a planilha e devolve a prévia. Não grava nada. */
export async function lerPlanilha(arquivo: File): Promise<PreviaImportacao> {
  const { data } = await api.post<PreviaImportacao>(`${BASE_URL}/ler`, formulario(arquivo), {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: TEMPO_LIMITE_MS,
  });
  return data;
}

/** Cria os produtos novos. Manda o mesmo arquivo: o servidor confere tudo de novo. */
export async function importarPlanilha(arquivo: File): Promise<ResultadoImportacaoPlanilha> {
  const { data } = await api.post<ResultadoImportacaoPlanilha>(`${BASE_URL}/importar`, formulario(arquivo), {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: TEMPO_LIMITE_MS,
  });
  return data;
}
