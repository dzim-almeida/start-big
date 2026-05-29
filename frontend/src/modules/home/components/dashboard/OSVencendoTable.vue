<script setup lang="ts">
import { ref } from 'vue';
import { AlertTriangle } from 'lucide-vue-next';
import { useOSCreateFlow } from '@/modules/order-service/ordens/composables/useOSCreateFlow';
import { getUniqueOS } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { useToast } from '@/shared/composables/useToast';
import type { OSVencendoItemData } from '../../schemas/dashboard.schema';

interface Props {
  items: OSVencendoItemData[];
  isLoading: boolean;
  isError: boolean;
}

defineProps<Props>();

const { openExistingOS } = useOSCreateFlow();
const toast = useToast();
const loadingOS = ref<string | null>(null);

async function handleRowClick(item: OSVencendoItemData) {
  if (loadingOS.value) return;

  loadingOS.value = item.numero_os;
  try {
    const osCompleta = await getUniqueOS(item.numero_os);
    openExistingOS(osCompleta);
  } catch {
    toast.error('Erro ao carregar detalhes da OS');
  } finally {
    loadingOS.value = null;
  }
}

const urgenciaConfig = {
  vermelho: {
    row: 'border-l-4 border-red-500 bg-red-50/50',
    badge: 'bg-red-50 text-red-600 border border-red-200',
    label: 'Vencida',
  },
  amarelo: {
    row: 'border-l-4 border-amber-400 bg-amber-50/30',
    badge: 'bg-amber-50 text-amber-600 border border-amber-200',
    label: 'Urgente',
  },
  verde: {
    row: 'border-l-4 border-emerald-400',
    badge: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    label: 'No prazo',
  },
};

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '...' : text;
}
</script>

<template>
  <div
    class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-hidden flex flex-col"
  >
    <!-- Header -->
    <div class="p-4 md:p-6 border-b border-zinc-100 flex items-center gap-2">
      <AlertTriangle :size="18" class="text-amber-500" />
      <h3 class="font-bold text-base md:text-lg text-zinc-900">Ordens Vencendo</h3>
    </div>

    <!-- Error -->
    <div v-if="isError" class="p-8 text-center text-red-500 text-sm flex-1 flex items-center justify-center">
      Erro ao carregar ordens de serviço
    </div>

    <!-- Loading -->
    <div v-else-if="isLoading" class="p-6 space-y-3 flex-1">
      <div v-for="i in 4" :key="i" class="h-12 bg-zinc-100 rounded-lg animate-pulse" />
    </div>

    <!-- Table -->
    <div v-else-if="items.length > 0" class="overflow-x-auto flex-1">
      <table class="w-full text-left min-w-80">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-5 py-3">N° OS</th>
            <th class="px-4 md:px-5 py-3">Cliente</th>
            <th class="px-4 md:px-5 py-3">Defeito</th>
            <th class="px-4 md:px-5 py-3">Previsão</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in items"
            :key="item.numero_os"
            :class="[
              'transition-colors cursor-pointer',
              urgenciaConfig[item.urgencia].row,
              loadingOS === item.numero_os ? 'opacity-60 pointer-events-none' : 'hover:brightness-95',
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
            <td
              class="px-4 md:px-5 py-3 text-xs text-zinc-500 max-w-48 truncate"
            >
              {{ truncate(item.defeito_relatado, 40) }}
            </td>
            <td class="px-4 md:px-5 py-3">
              <div class="flex items-center gap-2">
                <span class="text-xs md:text-sm font-medium text-zinc-700">
                  {{ formatDate(item.data_previsao) }}
                </span>
                <span
                  :class="[
                    'px-2 py-0.5 rounded-full text-[9px] md:text-[10px] font-bold whitespace-nowrap',
                    urgenciaConfig[item.urgencia].badge,
                  ]"
                >
                  {{ urgenciaConfig[item.urgencia].label }}
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-else class="p-8 text-center text-zinc-400 text-sm flex-1 flex items-center justify-center">
      Nenhuma OS com previsão pendente
    </div>
  </div>
</template>
