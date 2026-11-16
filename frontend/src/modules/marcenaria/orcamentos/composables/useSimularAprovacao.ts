/**
 * @fileoverview Prévia da aprovação no AprovarModal (Spec 08B D3).
 *
 * Cada mudança (caixa de móvel, instalação, desconto) pede os números ao
 * backend 400 ms depois. Nada é calculado em TypeScript (C8). Enquanto carrega,
 * o último número fica na tela (esmaecido); erro de desconto vai para o campo.
 */
import { computed, type Ref } from 'vue';
import { keepPreviousData, useQuery } from '@tanstack/vue-query';
import { refDebounced } from '@vueuse/core';

import { CHAVE_RAIZ, ESPERA_PREVIA_MS } from '../constants/orcamento.constants';
import type { AprovacaoEntrada } from '../schemas/aprovacao.schema';
import { simularAprovacao } from '../services/aprovacao.service';

export function useSimularAprovacao(orcamentoId: Ref<number | null>, entrada: Ref<AprovacaoEntrada>, ativo: Ref<boolean>) {
  // Uma cópia simples (sem reatividade) para a chave da query e a espera.
  const corpo = computed<AprovacaoEntrada>(() => JSON.parse(JSON.stringify(entrada.value)));
  const corpoEsperado = refDebounced(corpo, ESPERA_PREVIA_MS);   // espera o usuário parar de mexer

  return useQuery({
    queryKey: computed(() => [CHAVE_RAIZ, 'simular-aprovacao', orcamentoId.value, corpoEsperado.value]),
    queryFn: () => simularAprovacao(orcamentoId.value!, corpoEsperado.value),
    // Sem móvel marcado não há o que simular (a API recusaria).
    enabled: computed(() => ativo.value && orcamentoId.value != null && corpoEsperado.value.movel_ids.length > 0),
    placeholderData: keepPreviousData,
    retry: false,
  });
}
