import type { SituacaoOrcamento } from '../types/fabrica.types';

/**
 * Espelha `AMBIENTES` de app/core/segmentos/definicoes/marcenaria.py — é
 * sugestão (datalist), não trava: o ambiente do orçamento aceita qualquer nome.
 */
export const AMBIENTES = [
  'Cozinha',
  'Dormitório',
  'Closet',
  'Banheiro',
  'Sala',
  'Escritório',
  'Área de serviço',
  'Outro',
] as const;

export const ROTULO_SITUACAO: Record<SituacaoOrcamento, { rotulo: string; classe: string }> = {
  RASCUNHO: { rotulo: 'Rascunho', classe: 'bg-zinc-50 text-zinc-600 border-zinc-200' },
  ENVIADO: { rotulo: 'Com o cliente', classe: 'bg-sky-50 text-sky-700 border-sky-200' },
  APROVADO: { rotulo: 'Aprovada', classe: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  RECUSADO: { rotulo: 'Recusada', classe: 'bg-red-50 text-red-700 border-red-200' },
  VENCIDO: { rotulo: 'Vencida', classe: 'bg-amber-50 text-amber-700 border-amber-200' },
};
