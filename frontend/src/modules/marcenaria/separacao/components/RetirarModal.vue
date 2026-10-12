<script setup lang="ts">
/**
 * @component RetirarModal
 * @description Retirar do estoque para a OS (Spec 10B D5).
 *
 * Abre com a quantidade JÁ preenchida (o que falta) e selecionada: Enter
 * confirma. Não trava nada (E2a), mas avisa ANTES:
 * - o estoque não cobre esta OS → aviso âmbar e "Retirar mesmo assim";
 * - mais do que falta → aviso "Acima do sugerido".
 */
import { computed, nextTick, ref, watch } from 'vue';
import { AlertTriangle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { LinhaSeparacao } from '../schemas/separacao.schema';
import { lerQuantidade, quantidadeComUnidade, quantidadeParaCampo } from '../utils/quantidades';

const props = defineProps<{
  isOpen: boolean;
  linha: LinhaSeparacao | null;
  /** Quanto já vem no campo (padrão: o que falta). */
  quantidadeInicial?: number | null;
  gravando: boolean;
}>();

const emit = defineEmits<{ close: []; confirmar: [quantidadeMilesimos: number] }>();

const texto = ref('');
const campo = ref<HTMLInputElement | null>(null);

// Abriu: preenche com a falta e SELECIONA, para digitar por cima ou dar Enter.
watch(() => props.isOpen, async (aberto) => {
  if (!aberto || !props.linha) return;
  const inicial = props.quantidadeInicial ?? props.linha.falta_milesimos;
  texto.value = inicial > 0 ? quantidadeParaCampo(inicial, props.linha.unidade) : '';
  await nextTick();
  campo.value?.focus();
  campo.value?.select();
}, { immediate: true });

const leitura = computed(() => (props.linha ? lerQuantidade(texto.value, props.linha.unidade) : null));
const quantidade = computed(() => (leitura.value && 'milesimos' in leitura.value ? leitura.value.milesimos : null));
const erro = computed(() => (leitura.value && 'erro' in leitura.value && texto.value.trim() ? leitura.value.erro : ''));

/** O que o estoque cobre para esta retirada: a conta do Compras; linha já completa, o saldo. */
const cobertura = computed(() => {
  const linha = props.linha;
  if (!linha) return 0;
  return linha.falta_milesimos > 0 ? linha.no_estoque_milesimos : linha.estoque_milesimos;
});
const estoqueInsuficiente = computed(() => quantidade.value != null && quantidade.value > cobertura.value);
const acimaDoSugerido = computed(() => quantidade.value != null && props.linha != null && quantidade.value > props.linha.falta_milesimos);

const q = (milesimos: number) => quantidadeComUnidade(milesimos, props.linha?.unidade ?? 'UN');

function confirmar() {
  if (quantidade.value == null || props.gravando) return;
  emit('confirmar', quantidade.value);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Retirar do estoque" :subtitle="linha?.descricao" size="sm" overlay @close="emit('close')">
    <form v-if="linha" class="flex flex-col gap-3" @submit.prevent="confirmar">
      <label class="flex flex-col gap-1 text-xs font-medium text-zinc-600">
        Quantidade ({{ linha.unidade.toLowerCase() }})
        <input
          ref="campo"
          v-model="texto"
          type="text"
          inputmode="decimal"
          class="w-40 rounded-lg border px-3 py-2 text-2xl font-bold tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          :class="erro ? 'border-red-400' : 'border-zinc-300'"
          aria-label="Quantidade a retirar"
          data-testid="quantidade-retirar"
        />
      </label>
      <p v-if="erro" class="text-xs text-red-600">{{ erro }}</p>
      <p class="text-xs text-zinc-500">Falta retirar {{ q(linha.falta_milesimos) }} · retirado {{ q(linha.separada_milesimos) }}</p>

      <p
        v-if="estoqueInsuficiente"
        class="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900"
        data-testid="aviso-estoque"
      >
        <AlertTriangle :size="14" class="mt-0.5 shrink-0" />
        Estoque insuficiente para esta OS: há {{ q(cobertura) }}. A retirada pode deixar o estoque negativo.
      </p>
      <p v-if="acimaDoSugerido" class="text-xs text-zinc-600" data-testid="aviso-acima">
        Acima do sugerido ({{ q(linha.falta_milesimos) }}): a OS passa a consumir o que for retirado.
      </p>
      <!-- Enter no campo confirma (o form envia) -->
      <button type="submit" class="hidden" aria-hidden="true" tabindex="-1" />
    </form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="quantidade == null" :is-loading="gravando" data-testid="confirmar-retirar" @click="confirmar">
          {{ estoqueInsuficiente ? 'Retirar mesmo assim' : 'Retirar' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
