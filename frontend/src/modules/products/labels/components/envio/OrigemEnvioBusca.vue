<script setup lang="ts">
/**
 * @fileoverview Escolha de "de onde vem o envio": uma venda finalizada recente.
 * O backend já filtra pelo que o usuário pode ver (exige permissão de vendas).
 */
import { computed, ref } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery } from '@tanstack/vue-query';
import { FileCheck2, ShoppingCart } from 'lucide-vue-next';

import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import type { OrigemEnvioItem } from '@/shared/etiquetas/envio';
import { formatPrintDate } from '@/shared/utils/print.utils';
import { buscarOrigensEnvio } from '../../services/envio.service';

const emit = defineEmits<{ selecionar: [origem: OrigemEnvioItem] }>();

const busca = ref<string | null>('');
const buscaDebounced = refDebounced(busca, 350);
const termo = computed(() => (buscaDebounced.value || '').trim() || undefined);

const { data, isLoading, isError } = useQuery({
  queryKey: ['etiquetas-envio-origens', termo],
  queryFn: () => buscarOrigensEnvio(termo.value),
  staleTime: 1000 * 30,
});

const origens = computed(() => data.value ?? []);
</script>

<template>
  <div class="space-y-3">
    <BaseSearchInput v-model="busca" placeholder="Buscar venda por número ou cliente..." />

    <div class="border border-zinc-100 rounded-xl divide-y divide-zinc-100 max-h-80 overflow-y-auto">
      <p v-if="isLoading" class="px-4 py-6 text-center text-sm text-zinc-400">Buscando...</p>
      <p v-else-if="isError" class="px-4 py-6 text-center text-sm text-red-500">Não foi possível buscar as vendas.</p>
      <p v-else-if="origens.length === 0" class="px-4 py-6 text-center text-sm text-zinc-400">
        Nenhuma venda finalizada encontrada.
      </p>
      <button
        v-for="o in origens"
        :key="`${o.tipo}-${o.id}`"
        type="button"
        class="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-zinc-50 cursor-pointer"
        @click="emit('selecionar', o)"
      >
        <span class="w-8 h-8 shrink-0 rounded-lg flex items-center justify-center bg-brand-primary/10 text-brand-primary">
          <ShoppingCart :size="15" />
        </span>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-zinc-800 truncate">
            Venda {{ o.numero }}
            <span class="font-normal text-zinc-500"> · {{ o.cliente_nome || 'Sem cliente' }}</span>
          </p>
          <p class="text-xs text-zinc-400">{{ formatPrintDate(o.data) }}</p>
        </div>
        <span
          v-if="o.tem_nfe"
          class="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200"
          title="Tem NF-e autorizada: dá para imprimir o DANFE Simplificado"
        >
          <FileCheck2 :size="11" />
          NF-e
        </span>
      </button>
    </div>
  </div>
</template>
