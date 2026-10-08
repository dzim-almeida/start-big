/**
 * @fileoverview Entrada de mercadoria pela XML da NF-e do fornecedor.
 */

import api from '@/api/axios';
import type { DecisaoItem, NotaPrevia, ResultadoImportacao } from '../types/nfeEntrada.types';

const BASE_URL = 'estoque/nfe-entrada' as const;

/** Lê o XML e devolve a prévia. Não grava nada. */
export async function lerNotaXml(xml: string): Promise<NotaPrevia> {
  const form = new FormData();
  form.append('arquivo', new Blob([xml], { type: 'text/xml' }), 'nota.xml');
  const { data } = await api.post<NotaPrevia>(`${BASE_URL}/ler`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/**
 * Dá entrada na nota. Manda o MESMO XML de novo: quantidade e custo o servidor
 * relê dele; daqui só vai a decisão de cada item.
 */
export async function importarNotaXml(payload: {
  xml: string;
  itens: DecisaoItem[];
  lancar_contas_pagar: boolean;
  /** Módulo Compras: liga a nota a um pedido aberto do fornecedor. */
  pedido_id?: number;
}): Promise<ResultadoImportacao> {
  const { data } = await api.post<ResultadoImportacao>(`${BASE_URL}/importar`, payload);
  return data;
}
