import { computed, toValue, type MaybeRefOrGetter } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';

import type { Porte, PorteCreate, PorteUpdate } from '../schemas/porte.schema';
import {
  atualizarPorte,
  criarPorte,
  getPortes,
  getServicosDoPorte,
} from '../services/portes.service';

/**
 * Portes da loja (Spec 02B do lava-rápido).
 *
 * Todas as queries têm `enabled` pela capacidade `preco_por_porte`: fora do
 * lava-rápido as rotas respondem 404 e os outros segmentos nem fazem a chamada
 * (mesmo cuidado da query de configuração da marcenaria).
 */
export const PORTES_KEY = 'lava-rapido-portes';
export const SERVICOS_DO_PORTE_KEY = 'lava-rapido-servicos-do-porte';

/** Todos os portes (inclusive os desativados), uma query só para a loja inteira. */
export function usePortesQuery() {
  const { temPrecoPorPorte } = useCapacidades();
  const query = useQuery({
    queryKey: [PORTES_KEY],
    queryFn: () => getPortes(true),
    enabled: temPrecoPorPorte,
    staleTime: 1000 * 60 * 5,                // muda pouco: só o dono edita
  });

  /** Portes ATIVOS de um tipo, na ordem dos botões. */
  function ativosDoTipo(tipo: string | null | undefined): Porte[] {
    return (query.data.value ?? [])
      .filter((p) => p.ativo && p.tipo_veiculo === tipo)
      .sort((a, b) => a.ordem - b.ordem || a.id - b.id);
  }

  return { ...query, ativosDoTipo };
}

/** Serviços com o preço do porte escolhido (botões da comanda). */
export function useServicosDoPorteQuery(porteId: MaybeRefOrGetter<number | null | undefined>) {
  const { temPrecoPorPorte } = useCapacidades();
  return useQuery({
    queryKey: computed(() => [SERVICOS_DO_PORTE_KEY, toValue(porteId)]),
    // Sem porte também lista (o porte é opcional): vem o preço do cadastro.
    queryFn: () => getServicosDoPorte(toValue(porteId) ?? null),
    enabled: computed(() => temPrecoPorPorte.value),
  });
}

/** Criar, renomear, reordenar e desativar porte; recarrega a lista no fim. */
export function usePortesMutations() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const recarregar = () => {
    queryClient.invalidateQueries({ queryKey: [PORTES_KEY] });
    queryClient.invalidateQueries({ queryKey: [SERVICOS_DO_PORTE_KEY] });
  };
  const avisarErro = (erro: AxiosError<ApiError>) =>
    toast.error(getErrorMessage(erro, 'Não foi possível salvar o porte.'));

  const criar = useMutation<Porte, AxiosError<ApiError>, PorteCreate>({
    mutationFn: criarPorte,
    onSuccess: recarregar,
    onError: avisarErro,
  });

  const atualizar = useMutation<Porte, AxiosError<ApiError>, { id: number; dados: PorteUpdate }>({
    mutationFn: ({ id, dados }) => atualizarPorte(id, dados),
    onSuccess: recarregar,
    onError: (erro) => {
      avisarErro(erro);
      recarregar();                           // volta a tela ao que está gravado
    },
  });

  return { criar, atualizar };
}
