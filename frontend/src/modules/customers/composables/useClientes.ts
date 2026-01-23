/**
 * ===========================================================================
 * ARQUIVO: useClientes.ts
 * MODULO: Clientes
 * DESCRICAO: Composable principal para gerenciar a listagem de clientes.
 *            Encapsula toda a logica de estado, filtros e busca em um unico
 *            lugar reutilizavel.
 * ===========================================================================
 *
 * O QUE ESTE COMPOSABLE FAZ:
 * 1. Busca clientes da API usando Vue Query (com cache automatico)
 * 2. Permite filtrar por tipo (PF/PJ/Todos)
 * 3. Permite buscar por texto (nome, email, documento)
 * 4. Calcula estatisticas (total, ativos, PF, PJ)
 *
 * COMO USAR:
 * ```vue
 * <script setup>
 * import { useClientes } from '../composables';
 *
 * const { clientes, stats, isLoading, setFilterTipo, setSearch } = useClientes();
 * </script>
 * ```
 *
 * ESTADOS RETORNADOS:
 * - clientes: Lista filtrada de clientes (computed)
 * - stats: Estatisticas { total, ativos, pf, pj }
 * - activeFilterTipo: Filtro atual ('todos' | 'PF' | 'PJ')
 * - searchQuery: Texto de busca atual
 * - isLoading: Se esta carregando da API
 *
 * ACOES DISPONIVEIS:
 * - setFilterTipo(tipo): Muda o filtro de tipo
 * - setSearch(query): Muda o texto de busca
 * - refetch(): Forca recarregamento da API
 * ===========================================================================
 */

import { ref, computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import type { Cliente, ClienteFormatted, FilterTipo, ClienteFilterStatus } from '../types/clientes.types';
import { getClientes } from '../services/cliente.service';


// ===========================================================================
// COMPOSABLE PRINCIPAL
// ===========================================================================

/**
 * Composable que gerencia a listagem de clientes
 * Centraliza estado, filtros, busca e estatisticas
 *
 * @returns Objeto com estados reativos e metodos para manipulacao
 */
export function useClientes() {
  // ===========================================================================
  // ESTADOS REATIVOS
  // ===========================================================================

  /**
   * Filtro de tipo ativo (PF, PJ ou todos)
   * Controlado pelos botoes de filtro na interface
   */
  const activeFilterTipo = ref<FilterTipo>('todos');

  /**
   * Filtro de status (ativos, inativos, todos)
   */
  const activeFilterStatus = ref<ClienteFilterStatus>('ativos');

  /**
   * Flag para buscar apenas ativos (usado em selects/modais de busca)
   */
  const onlyActive = ref(false);

  /**
   * Texto de busca digitado pelo usuario
   * Usado para filtrar por nome, email ou documento
   */
  const searchQuery = ref('');

  /**
   * Paginacao
   */
  const currentPage = ref(1);
  const itemsPerPage = 10;

  // ===========================================================================
  // QUERY DA API (Vue Query)
  // ===========================================================================

  /**
   * Busca clientes da API
   * - queryKey inclui filtros para refetch automatico
   */
  const { data: clientesData, isLoading, refetch } = useQuery<Cliente[]>({
    queryKey: ['clientes', activeFilterStatus], // Recarrega se alterar o filtro de status
    queryFn: async () => {
      const result = await getClientes(searchQuery.value, activeFilterStatus.value);
      return result;
    },
  });

  // ===========================================================================
  // COMPUTED: LISTA FILTRADA
  // ===========================================================================

  /**
   * Lista de clientes ja filtrada por tipo e busca localmente
   * O filtro de status ja foi aplicado no backend
   */
  const clientesFiltrados = computed(() => {
    // Comeca com os dados retornados pela API (que ja estao filtrados por STATUS)
    let result = clientesData.value || [];

    // PASSO 1: Filtrar por Tipo (PF/PJ)
    if (activeFilterTipo.value !== 'todos') {
      result = result.filter(c => c.tipo === activeFilterTipo.value);
    }

    // PASSO 2: Filtrar por Busca (texto)
    // Busca local refinada ou apenas para quando nao quisermos fazer debounce na API
    // (Atualmente a API tambem busca, mas filtrar aqui garante reatividade imediata)
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase().trim();
      const queryNumbers = query.replace(/\D/g, ''); 
      
      result = result.filter(c => {
        const nome = c.tipo === 'PF' ? c.nome : c.nome_fantasia;
        const doc = c.tipo === 'PF' ? c.cpf : c.cnpj;

        if (nome && nome.toLowerCase().includes(query)) return true;
        if (c.email && c.email.toLowerCase().includes(query)) return true;
        if (doc && queryNumbers && doc.includes(queryNumbers)) return true;
        
        if (queryNumbers) {
          if (c.celular && c.celular.replace(/\D/g, '').includes(queryNumbers)) return true;
          if (c.telefone && c.telefone.replace(/\D/g, '').includes(queryNumbers)) return true;
        }

        return false;
      });
    }

    return result;
  });

  // ===========================================================================
  // COMPUTED: FORMATACAO
  // ===========================================================================

  const clientesFormatados = computed<ClienteFormatted[]>(() => {
    const lista = clientesFiltrados.value;
    if (!lista || !Array.isArray(lista)) return [];

    const mapped = lista.map((cliente) => {
      const c = cliente as any;
      const name = cliente.tipo === 'PF' ? c.nome : c.nome_fantasia;

      return {
        ...cliente,
        displayName: name || 'Sem Nome',
        displayDoc: cliente.tipo || '',
        displayPhone: cliente.celular || cliente.telefone || '',
        initial: name ? name.charAt(0).toUpperCase() : '?',
        sortName: (name || '').toLowerCase(),
      } as ClienteFormatted;
    });

    return mapped.sort((a, b) => a.sortName.localeCompare(b.sortName, 'pt-BR'));
  });

  // ===========================================================================
  // COMPUTED: PAGINACAO
  // ===========================================================================

  const totalItems = computed(() => clientesFormatados.value.length);
  const totalPages = computed(() => Math.ceil(totalItems.value / itemsPerPage));

  const paginatedClientes = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return clientesFormatados.value.slice(start, end);
  });

  // ===========================================================================
  // COMPUTED: ESTATISTICAS
  // ===========================================================================

  const stats = computed(() => {
    const data = clientesData.value || [];
    return {
      total: data.length,                        
      ativos: data.filter(c => c.ativo).length,  
      pf: data.filter(c => c.tipo === 'PF').length, 
      pj: data.filter(c => c.tipo === 'PJ').length, 
    };
  });

  // ===========================================================================
  // ACOES (MUTADORES DE ESTADO)
  // ===========================================================================

  function setFilterTipo(tipo: FilterTipo): void {
    activeFilterTipo.value = tipo;
    currentPage.value = 1;
  }

  function setFilterStatus(status: ClienteFilterStatus): void {
    activeFilterStatus.value = status;
    currentPage.value = 1;
  }

  function setSearch(query: string): void {
    searchQuery.value = query;
    // Opcional: chamar refetch() aqui se quiser busca server-side exclusiva
    // mas por enquanto mantemos a busca hibrida (client filtra tambem pra ser rapido)
    refetch();
    currentPage.value = 1;
  }

  function setOnlyActive(value: boolean): void {
    onlyActive.value = value;
    if (value) {
      activeFilterStatus.value = 'ativos';
    }
  }

  // ===========================================================================
  // RETORNO DO COMPOSABLE
  // ===========================================================================

  return {
    // Estados reativos
    clientes: paginatedClientes, 
    totalItems,
    totalPages,
    currentPage,
    
    // Outros estados
    stats,              
    activeFilterTipo,
    activeFilterStatus, 
    searchQuery,        
    isLoading,          

    // Acoes
    setFilterTipo,
    setFilterStatus,
    setSearch,
    setOnlyActive,
    refetch,
    setPage: (page: number) => currentPage.value = page,
  };
}
