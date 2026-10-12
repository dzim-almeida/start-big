<script setup lang="ts">
/**
 * @component DevolverModal
 * @description Devolver ao estoque a sobra (Spec 10B; 10A D9).
 *
 * "Devolver" quer dizer "isto não vai ser usado nesta OS": volta para a
 * prateleira e a OS deixa de precisar. Até o que foi retirado.
 */
import { computed, nextTick, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { LinhaSeparacao } from '../schemas/separacao.schema';
import { lerQuantidade, quantidadeComUnidade } from '../utils/quantidades';

const props = defineProps<{ isOpen: boolean; linha: LinhaSeparacao | null; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [quantidadeMilesimos: number] }>();

const texto = ref('');
const campo = ref<HTMLInputElement | null>(null);

// Abriu: campo vazio e focado (a sobra é o usuário quem sabe).
watch(() => props.isOpen, async (aberto) => {
  if (!aberto) return;
  texto.value = '';
  await nextTick();
  campo.value?.focus();
}, { immediate: true });

const leitura = computed(() => (props.linha ? lerQuantidade(texto.value, props.linha.unidade) : null));
const erro = computed(() => {
  if (!props.linha || !texto.value.trim() || !leitura.value) return '';
  if ('erro' in leitura.value) return leitura.value.erro;
  return leitura.value.milesimos > props.linha.separada_milesimos
    ? `Não é possível devolver mais do que foi retirado (${q(props.linha.separada_milesimos)}).`
    : '';
});
const quantidade = computed(() =>
  !erro.value && leitura.value && 'milesimos' in leitura.value ? leitura.value.milesimos : null,
);

const q = (milesimos: number) => quantidadeComUnidade(milesimos, props.linha?.unidade ?? 'UN');

function confirmar() {
  if (quantidade.value == null || props.gravando) return;
  emit('confirmar', quantidade.value);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Devolver ao estoque" :subtitle="linha?.descricao" size="sm" overlay @close="emit('close')">
    <form v-if="linha" class="flex flex-col gap-3" @submit.prevent="confirmar">
      <label class="flex flex-col gap-1 text-xs font-medium text-zinc-600">
        Quantidade a devolver ({{ linha.unidade.toLowerCase() }})
        <input
          ref="campo"
          v-model="texto"
          type="text"
          inputmode="decimal"
          class="w-40 rounded-lg border px-3 py-2 text-2xl font-bold tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          :class="erro ? 'border-red-400' : 'border-zinc-300'"
          aria-label="Quantidade a devolver"
          data-testid="quantidade-devolver"
        />
      </label>
      <p v-if="erro" class="text-xs text-red-600" data-testid="erro-devolver">{{ erro }}</p>
      <p class="text-xs text-zinc-500">
        Retirado até agora: {{ q(linha.separada_milesimos) }}. O que voltar ao estoque deixa de ser consumido por esta OS.
      </p>
      <button type="submit" class="hidden" aria-hidden="true" tabindex="-1" />
    </form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="quantidade == null" :is-loading="gravando" data-testid="confirmar-devolver" @click="confirmar">
          Devolver
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
