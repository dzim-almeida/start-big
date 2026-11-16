/**
 * @fileoverview O orçamento que gerou a OS (aba "Orçamento" da OS, Spec 08B
 * D19-D23). Só chama a API com a aba ABERTA: as OS dos outros segmentos nunca
 * chamam `/marcenaria/...` (a aba nem existe lá).
 */
import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { CHAVE_RAIZ } from '../constants/orcamento.constants';
import { getResumoPorOs } from '../services/aprovacao.service';
import { statusDoErro } from '../utils/erros';

export function useOrcamentoDaOS(numeroOs: Ref<string | null>, ativo: Ref<boolean> = computed(() => true)) {
  const consulta = useQuery({
    queryKey: computed(() => [CHAVE_RAIZ, 'por-os', numeroOs.value]),
    queryFn: () => getResumoPorOs(numeroOs.value!),
    enabled: computed(() => ativo.value && !!numeroOs.value),
    retry: false,                                    // 404 (OS sem orçamento) não melhora repetindo
  });
  /** A OS não veio de um orçamento (D23): não é erro, é uma resposta. */
  const semOrcamento = computed(() => statusDoErro(consulta.error.value) === 404);
  return { ...consulta, semOrcamento };
}
