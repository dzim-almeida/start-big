<script setup lang="ts">
/**
 * @component EnviarModal
 * @description Enviar o orçamento ao cliente (Spec 06B D36, §7.9).
 *
 * - Faltando algo: lista SÓ o que falta, com link para o bloco que resolve.
 * - Completo: confirma mostrando total, sinal, validade e os avisos do motor
 *   (os avisos não bloqueiam: são a última chance de corrigir um insumo sem custo).
 *
 * O espaço `<slot name="proposta">` acima dos botões é da Spec 07
 * ("Enviar e gerar proposta").
 */
import { computed } from 'vue';
import { AlertTriangle, ArrowRight } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { textosDosAvisos } from '../../constants/avisos.constants';
import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { pendenciasParaEnviar, type PendenciaEnvio } from '../../utils/pendenciasEnvio';

const props = defineProps<{
  isOpen: boolean;
  detalhe: OrcamentoDetalhe;
  enviando: boolean;
}>();

const emit = defineEmits<{
  close: [];
  enviar: [];
  irPara: [bloco: PendenciaEnvio['bloco']];
}>();

const pendencias = computed(() => pendenciasParaEnviar(props.detalhe));
const avisos = computed(() => textosDosAvisos(props.detalhe.avisos, props.detalhe.inclui_custos));

/** "vale até 24/10/2026 (15 dias)": a validade começa a contar no envio. */
const validadeTexto = computed(() => {
  const dias = props.detalhe.parametros.validade_dias;
  const ate = new Date();
  ate.setDate(ate.getDate() + dias);                     // data local de hoje + os dias de validade
  return `vale até ${ate.toLocaleDateString('pt-BR')} (${dias} ${dias === 1 ? 'dia' : 'dias'})`;
});

const calculo = computed(() => props.detalhe.calculo);
</script>

<template>
  <BaseModal :is-open="isOpen" :title="pendencias.length ? 'Falta pouco para enviar' : 'Enviar ao cliente'" size="md" @close="emit('close')">
    <!-- O que falta (D36) -->
    <div v-if="pendencias.length" data-testid="pendencias-envio">
      <p class="mb-3 text-sm text-zinc-600">Antes de enviar:</p>
      <ul class="flex flex-col gap-2">
        <li v-for="pendencia in pendencias" :key="pendencia.texto">
          <button
            type="button"
            class="inline-flex items-center gap-1.5 text-sm font-medium text-brand-primary hover:underline cursor-pointer"
            @click="emit('irPara', pendencia.bloco)"
          >
            <ArrowRight :size="14" /> {{ pendencia.texto }}
          </button>
        </li>
      </ul>
    </div>

    <!-- Completo: confirmação com os números (vêm da API) -->
    <div v-else class="flex flex-col gap-4" data-testid="confirmacao-envio">
      <dl class="grid grid-cols-2 gap-2 text-sm">
        <dt class="text-zinc-500">Total</dt>
        <dd class="text-right font-semibold tabular-nums text-zinc-900">{{ formatCurrency(calculo.total_centavos) }}</dd>
        <template v-if="calculo.sinal_centavos">
          <dt class="text-zinc-500">Sinal</dt>
          <dd class="text-right tabular-nums text-zinc-800">{{ formatCurrency(calculo.sinal_centavos) }}</dd>
        </template>
        <dt class="text-zinc-500">Validade</dt>
        <dd class="text-right text-zinc-800">{{ validadeTexto }}</dd>
      </dl>

      <div v-if="avisos.length" class="flex flex-col gap-2">
        <p
          v-for="aviso in avisos"
          :key="aviso.codigo"
          class="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900"
        >
          <AlertTriangle :size="14" class="mt-0.5 shrink-0" /> {{ aviso.texto }}
        </p>
      </div>

      <!-- Spec 07: "Enviar e gerar proposta" -->
      <slot name="proposta" />
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">{{ pendencias.length ? 'Fechar' : 'Cancelar' }}</BaseButton>
        <BaseButton v-if="!pendencias.length" variant="primary" :is-loading="enviando" data-testid="confirmar-envio" @click="emit('enviar')">
          Enviar
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
