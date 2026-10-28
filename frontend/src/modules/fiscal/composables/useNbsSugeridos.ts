import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys } from '../constants/fiscal.constants';

/**
 * Os NBS que cabem no código de tributação nacional escolhido.
 *
 * Vem da correlação oficial da Receita (Anexo VIII), embarcada no backend: é o
 * que responde ao "não sei qual é o meu NBS". A tabela só muda com versão nova
 * do portal (e instalador novo), então a resposta não envelhece na sessão.
 *
 * Falha (sem módulo, sem tabela) devolve lista vazia: o campo NBS continua
 * aceitando busca livre e digitação direta.
 */
export function useNbsSugeridos(codigoNacional: Ref<string>, habilitado: Ref<boolean> | boolean = true) {
  const codigoCompleto = computed(() => (/^\d{6}$/.test(codigoNacional.value) ? codigoNacional.value : ''));

  const { data } = useQuery({
    queryKey: computed(() => fiscalKeys.nbsSugeridos(codigoCompleto.value)),
    queryFn: () => fiscalService.buscarNbs('', codigoCompleto.value),
    staleTime: Infinity,
    retry: false,
    enabled: computed(() => !!codigoCompleto.value && (typeof habilitado === 'boolean' ? habilitado : habilitado.value)),
  });

  return computed(() => (codigoCompleto.value ? data.value?.sugeridos ?? [] : []));
}
