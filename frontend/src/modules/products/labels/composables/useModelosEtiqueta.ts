/**
 * @fileoverview Modelos de etiqueta: os presets de fábrica (código) + os da
 * loja (banco), num único seletor.
 */

import { computed } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import type { ApiError } from '@/shared/types/axios.types';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { PRESETS } from '@/shared/etiquetas/presets';
import type { ModeloEtiqueta } from '@/shared/etiquetas/modelo';
import {
  createModeloEtiqueta,
  deleteModeloEtiqueta,
  getModelosEtiqueta,
  updateModeloEtiqueta,
} from '../services/modeloEtiqueta.service';
import type { ModeloEtiquetaApi, ModeloEtiquetaPayload } from '../types/etiquetas.types';
import { MODELOS_ETIQUETA_QUERY_KEY, MODELOS_ETIQUETA_STALE_TIME } from '../../shared/constants/queryKeys';

export function modeloDaLoja(api: ModeloEtiquetaApi): ModeloEtiqueta {
  return { chave: `loja:${api.id}`, id: api.id, nome: api.nome, fonte: api.fonte, definicao: api.definicao };
}

export function useModelosEtiqueta() {
  const query = useQuery({
    queryKey: [MODELOS_ETIQUETA_QUERY_KEY],
    queryFn: getModelosEtiqueta,
    staleTime: MODELOS_ETIQUETA_STALE_TIME,
  });

  const modelosDaLoja = computed(() => (query.data.value ?? []).map(modeloDaLoja));
  // Os da loja primeiro: quem criou um modelo quer achá-lo sem rolar os presets.
  const todos = computed<ModeloEtiqueta[]>(() => [...modelosDaLoja.value, ...PRESETS]);

  return { ...query, modelosDaLoja, todos };
}

export function useSalvarModeloEtiqueta() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<ModeloEtiquetaApi, AxiosError<ApiError>, { id: number | null; payload: ModeloEtiquetaPayload }>({
    mutationFn: ({ id, payload }) => (id ? updateModeloEtiqueta(id, payload) : createModeloEtiqueta(payload)),
    onSuccess: (_, { id }) => {
      toast.success(id ? 'Modelo atualizado' : 'Modelo criado', 'Ele já aparece em todos os terminais da loja.');
      queryClient.invalidateQueries({ queryKey: [MODELOS_ETIQUETA_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao salvar o modelo de etiqueta') as string);
    },
  });
}

export function useExcluirModeloEtiqueta() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<void, AxiosError<ApiError>, number>({
    mutationFn: deleteModeloEtiqueta,
    onSuccess: () => {
      toast.success('Modelo excluído');
      queryClient.invalidateQueries({ queryKey: [MODELOS_ETIQUETA_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao excluir o modelo de etiqueta') as string);
    },
  });
}
