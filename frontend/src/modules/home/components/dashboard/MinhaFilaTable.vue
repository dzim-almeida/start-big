<script setup lang="ts">
import { ref } from 'vue';
import { ClipboardList } from 'lucide-vue-next';
import { useOSCreateFlow } from '@/modules/order-service/ordens/composables/useOSCreateFlow';
import { getUniqueOS } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { useToast } from '@/shared/composables/useToast';
import type { MinhaFilaItemData } from '../../schemas/dashboard.schema';

interface Props {
  items: MinhaFilaItemData[];
  isLoading: boolean;
  isError: boolean;
}

defineProps<Props>();

const { openExistingOS } = useOSCreateFlow();
const toast = useToast();
const loadingOS = ref<string | null>(null);

async function handleRowClick(item: MinhaFilaItemData) {
  if (loadingOS.value) return;
  loadingOS.value = item.numero_os;
  try {
    const osCompleta = await getUniqueOS(item.numero_os);
    openExistingOS(osCompleta);
  } catch {
    toast.error('Erro ao carregar OS');
  } finally {
    loadingOS.value = null;
  }
}

const prioridadeConfig: Record<string, { label: string; class: string }> = {
  URGENTE: { label: 'Urgente', class: 'bg-red-50 text-red-600 border border-red-200' },
  ALTA:    { label: 'Alta',    class: 'bg-orange-50 text-orange-600 border border-orange-200' },
  NORMAL:  { label: 'Normal',  class: 'bg-zinc-100 text-zinc-600 border border-zinc-200' },
  BAIXA:   { label: 'Baixa',   class: 'bg-zinc-50 text-zinc-400 border border-zinc-200' },
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '...' : text;
}
</script>

<template>
  <div class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-hidden flex flex-col">
    <div class="p-4 md:p-6 border-b border-zinc-100 flex items-center gap-2">
      <ClipboardList :size="18" class="text-zinc-500" />
      <h3 class="font-bold text-base md:text-lg text-zinc-900">Minha Fila</h3>
      <span v-if="items.length > 0" class="ml-auto text-xs font-semibold bg-zinc-100 text-zinc-500 px-2 py-0.5 rounded-full">
        {{ items.length }}
      </span>
    </div>

    <div v-if="isError" class="p-8 text-center text-red-500 text-sm flex-1 flex items-center justify-center">
      Erro ao carregar fila de trabalho
    </div>

    <div v-else-if="isLoading" class="p-6 space-y-3 flex-1">
      <div v-for="i in 4" :key="i" class="h-12 bg-zinc-100 rounded-lg animate-pulse" />
    </div>

    <div v-else-if="items.length > 0" class="overflow-x-auto flex-1">
      <table class="w-full text-left min-w-80">
        <thead>
          <tr class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100">
            <th class="px-4 md:px-5 py-3">N° OS</th>
            <th class="px-4 md:px-5 py-3">Cliente</th>
            <th class="px-4 md:px-5 py-3">Defeito</th>
            <th class="px-4 md:px-5 py-3">Prioridade</th>
            <th class="px-4 md:px-5 py-3">Prazo</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="item in items"
            :key="item.numero_os"
            :class="[
              'transition-colors cursor-pointer hover:bg-zinc-50/60',
              loadingOS === item.numero_os ? 'opacity-60 pointer-events-none' : '',
            ]"
            role="button"
            tabindex="0"
            @click="handleRowClick(item)"
            @keydown.enter="handleRowClick(item)"
          >
            <td class="px-4 md:px-5 py-3 text-xs md:text-sm font-semibold text-zinc-700">
              {{ item.numero_os }}
            </td>
            <td class="px-4 md:px-5 py-3 text-xs md:text-sm text-zinc-600 truncate max-w-28">
              {{ item.cliente_nome }}
            </td>
            <td class="px-4 md:px-5 py-3 text-xs text-zinc-500 max-w-40 truncate">
              {{ truncate(item.defeito_relatado, 35) }}
            </td>
            <td class="px-4 md:px-5 py-3">
              <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold whitespace-nowrap', prioridadeConfig[item.prioridade]?.class ?? 'bg-zinc-100 text-zinc-500']">
                {{ prioridadeConfig[item.prioridade]?.label ?? item.prioridade }}
              </span>
            </td>
            <td class="px-4 md:px-5 py-3 text-xs text-zinc-600 whitespace-nowrap">
              {{ formatDate(item.data_previsao) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="p-8 text-center text-zinc-400 text-sm flex-1 flex items-center justify-center">
      Nenhuma OS em aberto
    </div>
  </div>
</template>
