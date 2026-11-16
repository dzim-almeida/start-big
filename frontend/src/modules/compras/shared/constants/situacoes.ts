/**
 * Situações do pedido de compra: rótulo e cor.
 *
 * As MESMAS cores no selo da tabela e no filtro (BaseFilter), senão o filtro e
 * a linha falariam línguas diferentes sobre o mesmo estado — mesma regra das
 * Contas a Pagar.
 */
import type { FilterOption } from '@/shared/types/filter.types';
import type { SituacaoPedido } from '../types/compras.types';

export const SITUACOES_PEDIDO: Record<SituacaoPedido, FilterOption> = {
  RASCUNHO: { label: 'Rascunho', class: 'bg-zinc-100 text-zinc-600 border border-zinc-200', color: 'bg-zinc-400' },
  ENVIADO: { label: 'Enviado', class: 'bg-blue-50 text-blue-700 border border-blue-200', color: 'bg-blue-500' },
  PARCIAL: { label: 'Recebido em parte', class: 'bg-amber-50 text-amber-700 border border-amber-200', color: 'bg-amber-500' },
  RECEBIDO: { label: 'Recebido', class: 'bg-emerald-50 text-emerald-700 border border-emerald-200', color: 'bg-emerald-500' },
  CANCELADO: { label: 'Cancelado', class: 'bg-zinc-100 text-zinc-400 border border-zinc-200 line-through', color: 'bg-zinc-300' },
};

/** O que aparece no histórico do pedido. Ação desconhecida cai no próprio código. */
export const ROTULO_ACAO: Record<string, string> = {
  CRIADO: 'Criado',
  EDITADO: 'Editado',
  ENVIADO: 'Enviado ao fornecedor',
  VOLTOU_RASCUNHO: 'Voltou a rascunho',
  CANCELADO: 'Cancelado',
  RECEBIDO: 'Mercadoria recebida',
  SALDO_ENCERRADO: 'Saldo encerrado',
};

export function codigoPedido(numero: number): string {
  return `PC-${String(numero).padStart(6, '0')}`;
}
