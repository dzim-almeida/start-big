<script setup lang="ts">
/**
 * @component OrcamentoStatusBadge
 * @description Selo colorido do status do orçamento (Spec 06B §7.8), na
 * mesma paleta dos selos de OS. Usado na lista e no cabeçalho do editor.
 */
import { computed } from 'vue';

import { STATUS_ORCAMENTO, type StatusOrcamento } from '../../constants/orcamento.constants';

const props = defineProps<{ status: StatusOrcamento }>();

// Rótulo e cores vêm da tabela de constantes: um lugar só para mudar.
const visual = computed(() => STATUS_ORCAMENTO[props.status]);
</script>

<template>
  <span
    class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap"
    :class="visual.classes"
    data-testid="status-orcamento"
  >
    {{ visual.rotulo }}
  </span>
</template>
