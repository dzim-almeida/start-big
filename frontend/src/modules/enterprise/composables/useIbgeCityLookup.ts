import { computed, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import axios from 'axios';
import { useToast } from '@/shared/composables/useToast';
import type { Ref } from 'vue';

interface IbgeCity {
  id: number;
  nome: string;
}

/**
 * Composable para lookup automático de código IBGE
 * Busca cidades de um estado e faz match com o nome da cidade
 *
 * @param cidade - Ref com nome da cidade
 * @param uf - Ref com sigla do estado (2 letras)
 * @returns codigoIbge, isLoading, cities
 */
export function useIbgeCityLookup(cidade: Ref<string>, uf: Ref<string>) {
  const toast = useToast();

  // Query para buscar cidades do estado
  const { data: cities, isLoading, isError } = useQuery({
    queryKey: ['ibge-cities', uf],
    queryFn: async () => {
      const { data } = await axios.get<IbgeCity[]>(
        `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf.value}/municipios`
      );
      return data;
    },
    enabled: computed(() => uf.value.length === 2),
    staleTime: 1000 * 60 * 60 * 24, // 24h cache
    retry: 2,
  });
  watch(isError, (hasError) => {
    if (hasError) toast.error('Erro ao buscar municipios do IBGE');
  });

  // Helper para normalização de strings (remove acentos)
  const normalize = (str: string) =>
    str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

  // Computed com match automático da cidade
  const codigoIbge = computed(() => {
    if (!cidade.value || !cities.value) return '';

    const target = normalize(cidade.value);
    const match = cities.value.find((c) => normalize(c.nome) === target);

    return match ? String(match.id) : '';
  });

  return {
    codigoIbge,
    isLoading,
    cities,
  };
}


