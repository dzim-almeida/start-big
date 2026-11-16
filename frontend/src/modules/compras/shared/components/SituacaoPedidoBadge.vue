<script setup lang="ts">
/** Selo da situação do pedido, com o "atrasado" por cima quando for o caso. */
import { SITUACOES_PEDIDO } from '../constants/situacoes';
import type { SituacaoPedido } from '../types/compras.types';

defineProps<{ situacao: SituacaoPedido; atrasado?: boolean }>();
</script>

<template>
  <span class="inline-flex items-center gap-1.5">
    <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="SITUACOES_PEDIDO[situacao].class">
      {{ SITUACOES_PEDIDO[situacao].label }}
    </span>
    <span
      v-if="atrasado"
      class="rounded-full bg-rose-50 px-2 py-0.5 text-[11px] font-semibold text-rose-700 border border-rose-200"
      title="Enviado e a previsão de entrega já passou"
    >
      Atrasado
    </span>
  </span>
</template>
