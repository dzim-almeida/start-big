/**
 * ===========================================================================
 * ARQUIVO: useOrdensServico.ts
 * MODULO: Ordem de Servico
 * DESCRICAO: Composable para gerenciar listagem, filtragem e paginacao de
 *            Ordens de Servico. Utiliza Vue Query para cache e sincronizacao.
 * ===========================================================================
 *
 * FUNCIONALIDADES:
 * - Busca paginada de OS com filtros (SERVER-SIDE)
 * - Filtro por status (enviado ao backend)
 * - Busca por texto (enviada ao backend)
 * - Paginacao server-side com metadados (total, pages)
 * - Estatisticas agregadas (total, abertas, em andamento, finalizadas)
 * - Persistencia do filtro de status no localStorage
 *
 * RETORNO:
 * - ordensServico: Lista de OS da pagina atual
 * - stats: Estatisticas de contagem por status
 * - activeFilterStatus: Filtro ativo atual
 * - searchQuery: Texto de busca
 * - isLoading, error: Estados de carregamento
 * - setFilterStatus, setSearch, setPage: Funcoes de controle
 * - currentPage, totalPages, totalItems: Metadados de paginacao
 * ===========================================================================
 */
import { ref, computed, watch } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery } from '@tanstack/vue-query';
import type { OrdemServicoListRead, OrdemServicoStatus } from '../types/ordemServico.types';
import type { PaginatedResponse } from '@/shared/types/axios.types';
import { ordemServicoService } from '../services/ordemServico.service';
import {
  STORAGE_KEY_OS_FILTER,
  OS_ITEMS_PER_PAGE,
  SEARCH_DEBOUNCE_MS,
  OS_LIST_STALE_TIME,
  OS_STATS_STALE_TIME,
} from '../constants';

export type FilterStatus = 'todos' | OrdemServicoStatus;

export function useOrdensServico() {
  // Inicializa com o valor salvo ou 'todos'
  const savedStatus = localStorage.getItem(STORAGE_KEY_OS_FILTER);
  const activeFilterStatus = ref<FilterStatus>((savedStatus as FilterStatus) || 'todos');

  // Texto de busca atual (input do usuario)
  const searchQuery = ref('');
  // Texto de busca com debounce (enviado ao server)
  const debouncedSearchQuery = refDebounced(searchQuery, SEARCH_DEBOUNCE_MS);
  const currentPage = ref(1);

  // Reset para primeira pagina ao buscar
  watch(debouncedSearchQuery, () => {
    currentPage.value = 1;
  });

  // Query com paginacao server-side
  const {
    data: paginatedData,
    isLoading,
    error,
    refetch,
  } = useQuery<PaginatedResponse<OrdemServicoListRead>>({
    queryKey: computed(() => [
      'ordens-servico',
      activeFilterStatus.value,
      debouncedSearchQuery.value,
      currentPage.value,
    ]),
    queryFn: () => ordemServicoService.getAll({
      status: activeFilterStatus.value,
      buscar: debouncedSearchQuery.value || undefined,
      page: currentPage.value,
      limit: OS_ITEMS_PER_PAGE,
    }),
    staleTime: OS_LIST_STALE_TIME,
  });

  // Items da pagina atual (vindos do server)
  const ordensServico = computed(() => paginatedData.value?.items || []);

  // Metadados de paginacao
  const totalItems = computed(() => paginatedData.value?.total || 0);
  const totalPages = computed(() => paginatedData.value?.pages || 0);

  // Estatisticas (Busca separada para nao depender do filtro da lista)
  const { data: statsData } = useQuery<Record<string, number>>({
    queryKey: ['ordens-servico-stats'],
    queryFn: () => ordemServicoService.getEstatisticas(),
    staleTime: OS_STATS_STALE_TIME,
  });

  const stats = computed(() => {
    const s = statsData.value || {};

    const total = Object.values(s).reduce((acc: number, val: number) => acc + (Number(val) || 0), 0);

    return {
      total,
      abertas: (s['ABERTA'] || 0),
      emAndamento: (s['EM_ANDAMENTO'] || 0) + (s['AGUARDANDO_PECAS'] || 0) + (s['AGUARDANDO_APROVACAO'] || 0) + (s['AGUARDANDO_RETIRADA'] || 0),
      finalizadas: (s['FINALIZADA'] || 0),
    };
  });

  function setFilterStatus(status: FilterStatus): void {
    activeFilterStatus.value = status;
    localStorage.setItem(STORAGE_KEY_OS_FILTER, status);
    currentPage.value = 1; // Reset para primeira pagina ao filtrar
  }

  function setSearch(query: string): void {
    searchQuery.value = query;
    // Reset de pagina eh feito no watch com debounce
  }

  function setPage(page: number): void {
    if (page >= 1 && (totalPages.value === 0 || page <= totalPages.value)) {
      currentPage.value = page;
    }
  }

  return {
    ordensServico,
    stats,
    activeFilterStatus,
    searchQuery,
    isLoading,
    error,
    setFilterStatus,
    setSearch,
    refetch,
    currentPage,
    totalPages,
    totalItems,
    setPage,
  };
}
