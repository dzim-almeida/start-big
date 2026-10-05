<script setup lang="ts">
/**
 * @fileoverview Escolher um insumo para a lista de material do móvel.
 *
 * Só aparecem produtos já marcados como insumo no cadastro (a rota
 * /fabrica/insumos filtra). Campo vazio lista os primeiros: a fábrica tem
 * poucas dezenas de insumos, e ver a lista ajuda a lembrar o nome.
 */
import { computed, ref, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { Plus } from 'lucide-vue-next';

import { fabricaKeys } from '../constants/queryKeys';
import { buscarInsumos } from '../services/fabrica.service';
import type { InsumoBusca } from '../types/fabrica.types';
import { ROTULO_CONSUMO } from '../utils/calculo';

const emit = defineEmits<{ escolher: [insumo: InsumoBusca] }>();

const termo = ref('');
const termoBuscado = ref('');
const aberto = ref(false);

let espera: ReturnType<typeof setTimeout> | undefined;
watch(termo, (valor) => {
  clearTimeout(espera);
  espera = setTimeout(() => (termoBuscado.value = valor.trim()), 250);
});

const { data, isFetching } = useQuery({
  queryKey: computed(() => fabricaKeys.buscaInsumo(termoBuscado.value)),
  queryFn: () => buscarInsumos(termoBuscado.value),
  enabled: aberto,
  staleTime: 30_000,
});

function escolher(insumo: InsumoBusca) {
  emit('escolher', insumo);
  termo.value = '';
  aberto.value = false;
}

function fecharDepois() {
  // Deixa o clique na opção acontecer antes de sumir com a lista.
  setTimeout(() => (aberto.value = false), 150);
}
</script>

<template>
  <div class="relative">
    <div class="flex items-center gap-2 rounded-lg border border-dashed border-zinc-300 px-2.5 bg-white focus-within:border-brand-primary">
      <Plus :size="14" class="text-zinc-400 shrink-0" />
      <input
        v-model="termo"
        type="text"
        class="w-full min-h-9 text-sm bg-transparent outline-none"
        placeholder="Adicionar material (MDF, fita, dobradiça…)"
        @focus="aberto = true"
        @blur="fecharDepois"
        @keydown.esc="aberto = false"
      />
    </div>
    <ul
      v-if="aberto"
      class="absolute z-20 mt-1 w-full max-h-64 overflow-auto rounded-lg border border-zinc-200 bg-white shadow-lg text-sm"
    >
      <li v-if="isFetching && !data" class="px-3 py-2 text-zinc-400">Buscando…</li>
      <li v-else-if="!data?.length" class="px-3 py-2 text-zinc-500">
        Nenhum insumo. Marque o produto como insumo no cadastro (seção "Insumo da fábrica").
      </li>
      <li
        v-for="insumo in data"
        :key="insumo.id"
        class="px-3 py-2 cursor-pointer hover:bg-brand-primary/5 flex justify-between gap-3"
        @mousedown.prevent="escolher(insumo)"
      >
        <span class="truncate">{{ insumo.nome }}</span>
        <span class="text-xs text-zinc-400 shrink-0">em {{ ROTULO_CONSUMO[insumo.unidade_consumo] }}</span>
      </li>
    </ul>
  </div>
</template>
