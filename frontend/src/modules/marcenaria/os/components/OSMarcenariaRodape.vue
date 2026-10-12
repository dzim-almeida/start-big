<script setup lang="ts">
/**
 * @component OSMarcenariaRodape
 * @description Rodapé do modal de OS da marcenaria (redesign 10/2026): o total
 * e o sinal à esquerda, e à direita o "Avançar para <próxima situação>" e as
 * ações de sempre da OS (slot: imprimir, reabrir, finalizar, salvar).
 *
 * "Avançar" grava SÓ o status (aplicarStatusSalvo, Spec 12B D13): o que foi
 * digitado em outra aba e ainda não salvo continua no formulário.
 */
import { computed, ref, toRef } from 'vue';
import { ArrowRight } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseStatusPill from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import { useToast } from '@/shared/composables/useToast';
import { formatCurrency } from '@/shared/utils/finance';
import { useOrcamentoDaOS } from '@/modules/marcenaria/orcamentos/composables/useOrcamentoDaOS';

import { proximoStatus } from '../utils/etapasOS';

const props = defineProps<{
  numeroOs: string | null;
  /** Total da OS, em centavos. */
  totalCentavos: number;
  status?: string | null;
  /** Rótulo de um status no vocabulário do segmento. */
  rotulo: (status: string) => string;
  /** OS finalizada/cancelada (ou travada): não avança. */
  travada: boolean;
  avancar: (status: string) => Promise<void>;
}>();

const toast = useToast();
const { data: orcamento } = useOrcamentoDaOS(toRef(props, 'numeroOs'));

/** O sinal: recebido (verde) ou só combinado na aprovação (âmbar, a receber). */
const sinal = computed(() => {
  const o = orcamento.value;
  if (!o) return null;
  if (o.sinal_recebido_centavos) return { tom: 'sucesso' as const, texto: `Sinal recebido: ${formatCurrency(o.sinal_recebido_centavos)}` };
  if (o.sinal_combinado_centavos) return { tom: 'alerta' as const, texto: `Sinal a receber: ${formatCurrency(o.sinal_combinado_centavos)}` };
  return null;
});

const proximo = computed(() => (props.travada ? null : proximoStatus(props.status)));
const avancando = ref(false);

async function avancarStatus() {
  if (!proximo.value) return;
  avancando.value = true;
  try {
    await props.avancar(proximo.value);
    toast.success(`OS movida para ${props.rotulo(proximo.value)}.`);
  } catch {
    toast.error('Não foi possível mudar a situação da OS. Tente de novo.');
  } finally {
    avancando.value = false;
  }
}
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-4" data-testid="rodape-os-marcenaria">
    <div class="flex flex-wrap items-center gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Total da OS</p>
        <p class="text-xl font-extrabold tabular-nums text-zinc-900">{{ formatCurrency(totalCentavos) }}</p>
      </div>
      <BaseStatusPill v-if="sinal" :tom="sinal.tom">{{ sinal.texto }}</BaseStatusPill>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <slot />
      <BaseButton
        v-if="proximo"
        variant="primary"
        size="sm"
        :is-loading="avancando"
        data-testid="avancar-status"
        @click="avancarStatus"
      >
        Avançar para {{ rotulo(proximo) }}
        <ArrowRight :size="16" class="ml-1.5" />
      </BaseButton>
    </div>
  </div>
</template>
