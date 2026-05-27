/**
 * @fileoverview Composables para movimentações de estoque
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import { useToast } from '@/shared/composables/useToast';
import { getMovimentacoes, createMovimentacao } from '../services/movimentacao.service';
import type { MovimentacaoCreate } from '../types/products.types';

export const MOVIMENTACOES_QUERY_KEY = 'movimentacoes-estoque';

export function useMovimentacoesQuery(produto_id?: number) {
  return useQuery({
    queryKey: [MOVIMENTACOES_QUERY_KEY, produto_id ?? null],
    queryFn: () => getMovimentacoes(produto_id),
    staleTime: 1000 * 30, // 30s — histórico muda com frequência
  });
}

export function useCreateMovimentacaoMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ produto_id, data }: { produto_id: number; data: MovimentacaoCreate }) =>
      createMovimentacao(produto_id, data),
    onSuccess: (result) => {
      const label = result.tipo === 'ENTRADA' ? 'Entrada' : result.tipo === 'SAIDA' ? 'Saída' : 'Ajuste';
      toast.success(`${label} registrada com sucesso!`);
      queryClient.invalidateQueries({ queryKey: [MOVIMENTACOES_QUERY_KEY] });
      // Invalida produtos para atualizar a quantidade exibida nos cards
      queryClient.invalidateQueries({ queryKey: ['produtos'] });
    },
    onError: () => {
      toast.error('Erro ao registrar movimentação. Verifique os dados.');
    },
  });
}