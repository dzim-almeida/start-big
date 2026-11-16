<script setup lang="ts">
/**
 * @component VersoesMenu
 * @description O rótulo "v2 ▾" do cabeçalho: abre a lista de TODAS as versões
 * do mesmo código (número, status, total, data) para abrir qualquer uma
 * (Spec 06B D42). O histórico do que foi oferecido fica a um clique.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { ChevronDown } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';
import { formatData } from '@/shared/utils/date.utils';

import { useVersoesQuery } from '../../composables/useOrcamentoQuery';
import OrcamentoStatusBadge from '../lista/OrcamentoStatusBadge.vue';

const props = defineProps<{ id: number; versao: number }>();
const emit = defineEmits<{ abrir: [id: number] }>();

const aberto = ref(false);
const raiz = ref<HTMLElement | null>(null);
onClickOutside(raiz, () => { aberto.value = false; });

// Só busca a lista quando o menu abre (quem não clica não paga a chamada).
const { data: versoes, isLoading } = useVersoesQuery(computed(() => props.id), aberto);

function escolher(id: number) {
  aberto.value = false;
  if (id !== props.id) emit('abrir', id);
}
</script>

<template>
  <div ref="raiz" class="relative">
    <button
      type="button"
      class="inline-flex items-center gap-0.5 rounded-md bg-zinc-100 px-2 py-0.5 text-xs font-bold text-zinc-700 hover:bg-zinc-200 cursor-pointer"
      aria-haspopup="menu"
      :aria-expanded="aberto"
      data-testid="menu-versoes"
      @click="aberto = !aberto"
    >
      v{{ versao }} <ChevronDown :size="12" />
    </button>

    <div v-if="aberto" role="menu" class="absolute left-0 z-30 mt-1 w-80 overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-lg">
      <p v-if="isLoading" class="px-4 py-3 text-xs text-zinc-400">Carregando versões…</p>
      <button
        v-for="item in versoes ?? []"
        :key="item.id"
        type="button"
        role="menuitem"
        class="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left hover:bg-zinc-50 cursor-pointer"
        :class="item.id === id ? 'bg-zinc-50' : ''"
        @click="escolher(item.id)"
      >
        <span>
          <span class="text-sm font-semibold text-zinc-800">v{{ item.versao }}</span>
          <span class="ml-2 text-[11px] text-zinc-400">{{ formatData(item.data_criacao) }}</span>
        </span>
        <span class="flex items-center gap-2">
          <span class="text-xs tabular-nums text-zinc-600">{{ formatCurrency(item.resumo_total_centavos) }}</span>
          <OrcamentoStatusBadge :status="item.status" />
        </span>
      </button>
    </div>
  </div>
</template>
