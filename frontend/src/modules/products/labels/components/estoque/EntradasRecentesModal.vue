<script setup lang="ts">
/**
 * @fileoverview "Etiquetas desta entrada" (plano, critério E3): as entradas de
 * estoque recentes, cada uma virando N etiquetas — N = quantidade que entrou.
 *
 * Quantidade fracionada (2,5 kg) sobe para o inteiro de cima: meia etiqueta
 * não existe, e faltar etiqueta é pior que sobrar uma.
 */
import { computed, ref, watch } from 'vue';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useMovimentacoesQuery } from '@/modules/products/inventory/composables/useMovimentacoesQuery';
import { MAX_POR_ITEM } from '../../store/filaEtiquetas.store';
import type { MovimentacaoRead } from '@/modules/products/inventory/types/products.types';

const props = defineProps<{
  isOpen: boolean;
  /** Ids dos produtos ativos: entrada de produto desativado não vira etiqueta. */
  idsAtivos: Set<number>;
}>();

const emit = defineEmits<{
  close: [];
  adicionar: [itens: { produtoId: number; quantidade: number; embalagemId: number | null }[]];
}>();

const { data, isLoading } = useMovimentacoesQuery();

const entradas = computed(() =>
  (data.value ?? []).filter((m) => m.tipo === 'ENTRADA' && m.quantidade > 0 && props.idsAtivos.has(m.produto_id)),
);

const selecionadas = ref<Set<number>>(new Set());

watch(
  () => props.isOpen,
  (aberto) => {
    if (aberto) selecionadas.value = new Set();
  },
);

const todasMarcadas = computed(
  () => entradas.value.length > 0 && entradas.value.every((m) => selecionadas.value.has(m.id)),
);

function alternar(id: number) {
  const novas = new Set(selecionadas.value);
  if (novas.has(id)) novas.delete(id);
  else novas.add(id);
  selecionadas.value = novas;
}

function alternarTodas() {
  selecionadas.value = todasMarcadas.value ? new Set() : new Set(entradas.value.map((m) => m.id));
}

// Entrada em caixa/fardo ("3 CX de 24"): etiqueta de cada unidade (72) ou da
// embalagem (3). O padrão é unidade — o que esta tela sempre fez.
const porEmbalagem = ref(false);
const temEntradaEmEmbalagem = computed(() => entradas.value.some((m) => m.embalagem_id && m.quantidade_embalagem));

function usaEmbalagem(m: MovimentacaoRead): boolean {
  return porEmbalagem.value && !!m.embalagem_id && !!m.quantidade_embalagem;
}

function etiquetasDa(m: MovimentacaoRead): number {
  const quantidade = usaEmbalagem(m) ? m.quantidade_embalagem! : m.quantidade;
  return Math.min(MAX_POR_ITEM, Math.ceil(quantidade));
}

const totalEtiquetas = computed(() =>
  entradas.value.filter((m) => selecionadas.value.has(m.id)).reduce((soma, m) => soma + etiquetasDa(m), 0),
);

function formatarData(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function formatarQuantidade(quantidade: number, unidade?: string | null): string {
  return `${quantidade.toLocaleString('pt-BR')} ${(unidade || 'un').toLowerCase()}`;
}

function confirmar() {
  const itens = entradas.value
    .filter((m) => selecionadas.value.has(m.id))
    .map((m) => ({
      produtoId: m.produto_id,
      quantidade: etiquetasDa(m),
      embalagemId: usaEmbalagem(m) ? m.embalagem_id! : null,
    }));
  emit('adicionar', itens);
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Entradas recentes"
    subtitle="Cada entrada vira uma etiqueta por unidade recebida"
    size="lg"
    @close="emit('close')"
  >
    <div v-if="isLoading" class="py-10 text-center text-sm text-zinc-400">Carregando entradas...</div>
    <div v-else-if="entradas.length === 0" class="py-10 text-center text-sm text-zinc-400">
      Nenhuma entrada de estoque recente.
    </div>
    <div v-if="temEntradaEmEmbalagem" class="flex flex-wrap items-center gap-3 mb-3 text-xs text-zinc-600">
      <span class="font-semibold">Entradas em caixa/fardo:</span>
      <label class="flex items-center gap-1.5 cursor-pointer">
        <input v-model="porEmbalagem" type="radio" :value="false" class="accent-brand-primary" />
        etiqueta de cada unidade
      </label>
      <label class="flex items-center gap-1.5 cursor-pointer">
        <input v-model="porEmbalagem" type="radio" :value="true" class="accent-brand-primary" />
        etiqueta da embalagem
      </label>
    </div>
    <div v-if="!isLoading && entradas.length" class="border border-zinc-100 rounded-xl overflow-hidden">
      <label class="flex items-center gap-3 px-4 py-2.5 bg-zinc-50 text-xs font-semibold text-zinc-600 cursor-pointer">
        <input type="checkbox" class="accent-brand-primary" :checked="todasMarcadas" @change="alternarTodas" />
        Marcar todas
      </label>
      <div class="divide-y divide-zinc-100 max-h-96 overflow-y-auto">
        <label
          v-for="mov in entradas"
          :key="mov.id"
          class="flex items-center gap-3 px-4 py-2.5 hover:bg-zinc-50/50 cursor-pointer"
        >
          <input type="checkbox" class="accent-brand-primary" :checked="selecionadas.has(mov.id)" @change="alternar(mov.id)" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-zinc-800 truncate">{{ mov.produto_nome }}</p>
            <p class="text-xs text-zinc-400">{{ formatarData(mov.created_at) }} · {{ mov.usuario_nome }}</p>
          </div>
          <div class="text-right shrink-0">
            <p class="text-sm font-semibold text-zinc-700">{{ formatarQuantidade(mov.quantidade, mov.unidade_medida) }}</p>
            <p v-if="mov.quantidade_embalagem && mov.embalagem_sigla" class="text-[11px] text-zinc-500">
              {{ mov.quantidade_embalagem }} {{ mov.embalagem_sigla }} de {{ mov.embalagem_fator }}
            </p>
            <p class="text-[11px] text-zinc-400">{{ etiquetasDa(mov) }} etiq.</p>
          </div>
        </label>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="selecionadas.size === 0" @click="confirmar">
          Adicionar {{ totalEtiquetas || '' }} {{ totalEtiquetas === 1 ? 'etiqueta' : 'etiquetas' }} à fila
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
