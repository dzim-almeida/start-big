<script setup lang="ts">
/**
 * @component FaixaAvisoRelogio
 * @description Faixa no topo de todas as telas quando o relógio do computador
 * voltou no tempo (LIC-08 §6.1, D-05, quadro 4).
 *
 * Só AVISA: o sistema continua funcionando. Não tem botão de fechar; ela some
 * sozinha quando o /licenca/status deixa de trazer o aviso (proposta aprovada).
 */

import { computed } from 'vue';
import { Clock } from 'lucide-vue-next';
import { useLicencaStatusQuery } from '@/shared/composables/useLicencaStatusQuery';

// A mesma consulta do badge do cabeçalho: o TanStack Query reaproveita o cache,
// então não há chamada a mais ao backend.
const { data } = useLicencaStatusQuery();

const relogioRecuou = computed(() => data.value?.aviso === 'relogio_recuou');
</script>

<template>
  <!-- role="status": leitores de tela anunciam o aviso sem roubar o foco -->
  <div
    v-if="relogioRecuou"
    role="status"
    class="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center gap-2.5"
  >
    <Clock :size="18" class="text-amber-700 shrink-0" aria-hidden="true" />
    <p class="text-[13px] text-amber-800">
      <strong class="font-semibold">O relógio deste computador está atrasado.</strong>
      Ajuste a data e a hora do Windows para a licença continuar funcionando sem internet.
    </p>
  </div>
</template>
