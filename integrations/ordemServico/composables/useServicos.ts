/**
 * ===========================================================================
 * ARQUIVO: useServicos.ts
 * MODULO: Ordem de Servico
 * DESCRICAO: Composable para gerenciar listagem, filtragem e paginacao do
 *            catalogo de Servicos. Utiliza Vue Query para cache.
 * ===========================================================================
 *
 * FUNCIONALIDADES:
 * - Busca paginada de servicos (SERVER-SIDE)
 * - Filtro por status (ativos, inativos, todos)
 * - Busca por descricao (enviada ao backend)
 * - Paginacao server-side com metadados (total, pages)
 * - Estatisticas: total, ativos, inativos, ticket medio
 *
 * RETORNO:
 * - servicos: Lista de servicos da pagina atual
 * - stats: Estatisticas agregadas
 * - searchQuery, statusFilter: Filtros ativos
 * - isLoading, error: Estados de carregamento
 * - setSearch, setFilter, setPage: Funcoes de controle
 * ===========================================================================
 */
import { ref, computed, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import type { ServicoRead } from '../types/servicos.types';
import type { PaginatedResponse } from '@/shared/types/axios.types';
import { getServicos, getServicosEstatisticas, type ServicosStats } from '../services/servicos.service';

export type StatusFilter = 'todos' | 'ativos' | 'inativos';

const ITEMS_PER_PAGE = 10;

export function useServicos() {
  const statusFilter = ref<StatusFilter>('todos');
  const searchQuery = ref('');
  const debouncedSearchQuery = ref('');
  const currentPage = ref(1);

  // Debounce para busca (evita requests excessivos enquanto digita)
  let searchTimeout: ReturnType<typeof setTimeout> | null = null;

  watch(searchQuery, (newValue) => {
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      debouncedSearchQuery.value = newValue;
      currentPage.value = 1;
    }, 300);
  });

  // Query com paginacao server-side
  const {
    data: paginatedData,
    isLoading,
    error,
    refetch,
  } = useQuery<PaginatedResponse<ServicoRead>>({
    queryKey: computed(() => [
      'servicos',
      statusFilter.value,
      debouncedSearchQuery.value,
      currentPage.value,
    ]),
    queryFn: () => getServicos({
      status: statusFilter.value,
      buscar: debouncedSearchQuery.value || undefined,
      page: currentPage.value,
      limit: ITEMS_PER_PAGE,
    }),
    staleTime: 1000 * 60 * 2, // 2 minutos
  });

  // Items da pagina atual
  const servicos = computed(() => paginatedData.value?.items || []);

  // Metadados de paginacao
  const totalItems = computed(() => paginatedData.value?.total || 0);
  const totalPages = computed(() => paginatedData.value?.pages || 0);

  // Query separada para estatisticas (endpoint dedicado no backend)
  const { data: statsData } = useQuery<ServicosStats>({
    queryKey: ['servicos-stats'],
    queryFn: () => getServicosEstatisticas(),
    staleTime: 1000 * 60 * 5, // 5 minutos
  });

  const stats = computed(() => {
    const data = statsData.value;
    return {
      total: data?.total || 0,
      ativos: data?.ativos || 0,
      inativos: data?.inativos || 0,
      mediaValor: data?.media_valor || 0,
    };
  });

  function setSearch(query: string): void {
    searchQuery.value = query;
  }

  function setFilter(status: StatusFilter): void {
    statusFilter.value = status;
    currentPage.value = 1;
  }

  function setPage(page: number): void {
    if (page >= 1 && (totalPages.value === 0 || page <= totalPages.value)) {
      currentPage.value = page;
    }
  }

  return {
    servicos,
    stats,
    searchQuery,
    statusFilter,
    isLoading,
    error,
    setSearch,
    setFilter,
    refetch,
    currentPage,
    totalPages,
    totalItems,
    setPage,
  };
}
