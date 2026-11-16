<script setup lang="ts">
/**
 * @component AvisoEntregaFinalizacao
 * @description O aviso da finalização da OS na marcenaria (Spec 13B D18; I3).
 *
 * Ambiente não entregue e pendência aberta AVISAM, mas não impedem finalizar:
 * o componente não emite nada para o modal, e o botão de finalizar não depende
 * dele. Só é montado com a capacidade `orcamento_tecnico` (D19): nos outros
 * segmentos não existe, e nenhuma chamada a `/marcenaria/...` é feita.
 */
import { computed, toRef } from 'vue';
import { AlertTriangle } from 'lucide-vue-next';

import { useResumoEntrega } from '../composables/useResumoEntrega';

const props = defineProps<{ numeroOs: string }>();

const { data: resumo } = useResumoEntrega(toRef(props, 'numeroOs'));

const ambientes = computed(() => resumo.value?.ambientes_pendentes ?? []);
const pendencias = computed(() => resumo.value?.pendencias_abertas ?? []);
</script>

<template>
  <!-- Âmbar e só informativo (o bloco de itens pendentes da oficina é que trava). -->
  <div
    v-if="ambientes.length || pendencias.length"
    class="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"
    role="status"
    data-testid="aviso-entrega"
  >
    <AlertTriangle :size="18" class="mt-0.5 shrink-0 text-amber-600" />
    <div class="space-y-1">
      <p v-if="ambientes.length" data-testid="aviso-ambientes">
        <strong>Ambientes ainda não entregues:</strong> {{ ambientes.join(', ') }}.
      </p>
      <p v-if="pendencias.length" data-testid="aviso-pendencias">
        <strong>Pendências abertas:</strong>
        {{ pendencias.map((p) => `${p.descricao} (${p.ambiente})`).join('; ') }}.
      </p>
      <p class="text-xs text-amber-800">Dá para finalizar mesmo assim.</p>
    </div>
  </div>
</template>
