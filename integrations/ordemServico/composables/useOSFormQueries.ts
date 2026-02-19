import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { getServicos } from '../services/servicos.service';
import { getProdutos, type ProdutoRead } from '../services/produtos.service';
import { getFuncionarios } from '../services/funcionario.service';
import type { FuncionarioResumo } from '../types/ordemServico.types';
import { SERVICE_STALE_TIME } from '../constants';

export interface SelectOption {
  value: string;
  label: string;
  preco?: number;
}

export function useOSFormQueries(isOpen: Ref<boolean> | (() => boolean)) {
  const enabled = computed(() => {
    return typeof isOpen === 'function' ? isOpen() : isOpen.value;
  });

  const { data: servicosData, isLoading: isLoadingServicos } = useQuery({
    queryKey: ['servicos-dropdown'],
    queryFn: async () => {
      const response = await getServicos({ limit: 1000 });
      return response.items;
    },
    enabled,
    staleTime: SERVICE_STALE_TIME,
  });

  const { data: funcionariosData, isLoading: isLoadingFuncionarios } = useQuery<FuncionarioResumo[]>({
    queryKey: ['funcionarios'],
    queryFn: () => getFuncionarios(),
    enabled,
    staleTime: SERVICE_STALE_TIME,
  });

  const { data: produtosData, isLoading: isLoadingProdutos } = useQuery<ProdutoRead[]>({
    queryKey: ['produtos'],
    queryFn: () => getProdutos(),
    enabled,
    staleTime: SERVICE_STALE_TIME,
  });

  const servicosOptions = computed<SelectOption[]>(() => {
    return (servicosData.value || [])
      .filter(s => s.ativo)
      .map(s => ({
        value: String(s.id),
        label: s.descricao,
        preco: s.valor,
      }));
  });

  const produtosOptions = computed<SelectOption[]>(() => {
    return (produtosData.value || [])
      .filter(p => p.ativo)
      .map(p => ({
        value: String(p.id),
        label: p.nome,
        preco: p.estoque?.valor_varejo || 0,
      }));
  });

  const funcionariosOptions = computed<SelectOption[]>(() => {
    return (funcionariosData.value || []).map(f => ({
      value: String(f.id),
      label: f.nome,
    }));
  });

  return {
    servicosData,
    funcionariosData,
    produtosData,
    servicosOptions,
    produtosOptions,
    funcionariosOptions,
    isLoadingServicos,
    isLoadingFuncionarios,
    isLoadingProdutos,
  };
}
