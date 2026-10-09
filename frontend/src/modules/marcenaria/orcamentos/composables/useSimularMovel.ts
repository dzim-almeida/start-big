/**
 * @fileoverview Prévia do preço no modal do móvel (Spec 06B D6, D30, §7.6).
 *
 * 400 ms depois da última digitação, manda o móvel para `/moveis/simular`
 * (nada é gravado). Enquanto a resposta não chega, o último número continua
 * na tela, esmaecido. Se falhar, a tela mostra "Prévia indisponível" e o
 * usuário salva mesmo assim.
 */
import { computed, type Ref } from 'vue';
import { keepPreviousData, useQuery } from '@tanstack/vue-query';
import { refDebounced } from '@vueuse/core';

import { CHAVE_RAIZ, ESPERA_PREVIA_MS } from '../constants/orcamento.constants';
import { movelSimulavel, paraApiMovel, type MovelForm } from '../schemas/movelForm.schema';
import { simularMovel } from '../services/orcamentoMovel.service';

/**
 * @param orcamentoId  orçamento dono dos parâmetros (markup, perda, custo/hora)
 * @param movel        o formulário aberto (reativo)
 * @param movelId      móvel gravado sendo editado (insumos com id mantêm o custo copiado)
 * @param incluiCustos quem vê custos manda mão de obra e valor da central
 */
export function useSimularMovel(
  orcamentoId: Ref<number | null>,
  movel: Ref<MovelForm>,
  movelId: Ref<number | null>,
  incluiCustos: Ref<boolean>,
) {
  // O corpo da API, recalculado a cada tecla (barato: só troca de unidade).
  const corpo = computed(() => paraApiMovel(movel.value, incluiCustos.value));
  // Espera o usuário parar de digitar antes de perguntar ao servidor.
  const corpoEsperado = refDebounced(corpo, ESPERA_PREVIA_MS);
  const simulavel = computed(() => movelSimulavel(movel.value));

  return useQuery({
    // O corpo entra na chave: a mesma combinação reaproveita a resposta.
    queryKey: computed(() => [CHAVE_RAIZ, 'simular', orcamentoId.value, movelId.value, corpoEsperado.value]),
    queryFn: () => simularMovel(orcamentoId.value!, corpoEsperado.value, movelId.value),
    enabled: computed(() => orcamentoId.value != null && simulavel.value),
    placeholderData: keepPreviousData,   // mantém o último número, esmaecido
    retry: false,                        // falhou: "Prévia indisponível" (D30)
    staleTime: 30_000,                   // mesma entrada não precisa perguntar de novo logo
  });
}
