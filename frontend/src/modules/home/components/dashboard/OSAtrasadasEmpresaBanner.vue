<script setup lang="ts">
import { ref } from 'vue';
import { AlertCircle, ChevronDown, ChevronUp } from 'lucide-vue-next';
import { useOSCreateFlow } from '@/modules/order-service/ordens/composables/useOSCreateFlow';
import { getUniqueOS } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { useToast } from '@/shared/composables/useToast';
import type { OSAtrasadaEmpresaItemData } from '../../schemas/dashboard.schema';

interface Props {
  items: OSAtrasadaEmpresaItemData[];
  total: number;
}

defineProps<Props>();

const expanded = ref(false);
const loadingOS = ref<string | null>(null);
const { openExistingOS } = useOSCreateFlow();
const toast = useToast();

async function handleClick(item: OSAtrasadaEmpresaItemData) {
  if (loadingOS.value) return;
  loadingOS.value = item.numero_os;
  try {
    const os = await getUniqueOS(item.numero_os);
    openExistingOS(os);
  } catch {
    toast.error('Erro ao carregar OS');
  } finally {
    loadingOS.value = null;
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('pt-BR');
}
</script>

<template>
  <div v-if="total > 0" class="bg-red-50 border border-red-200 rounded-2xl overflow-hidden">
    <button
      class="w-full flex items-center gap-3 px-4 md:px-6 py-3 text-left hover:bg-red-100/50 transition-colors"
      @click="expanded = !expanded"
    >
      <AlertCircle :size="18" class="text-red-500 shrink-0" />
      <span class="text-sm font-bold text-red-700 flex-1">
        {{ total }} OS com prazo vencido na empresa
      </span>
      <component :is="expanded ? ChevronUp : ChevronDown" :size="16" class="text-red-400 shrink-0" />
    </button>

    <div v-if="expanded" class="border-t border-red-200 divide-y divide-red-100">
      <button
        v-for="item in items"
        :key="item.numero_os"
        :class="[
          'w-full flex items-center gap-3 px-4 md:px-6 py-3 text-left transition-colors hover:bg-red-100/40',
          loadingOS === item.numero_os ? 'opacity-60 pointer-events-none' : '',
        ]"
        @click="handleClick(item)"
      >
        <div class="flex-1 min-w-0">
          <span class="text-xs font-bold text-red-700 mr-2">{{ item.numero_os }}</span>
          <span class="text-xs text-red-600">{{ item.cliente_nome }}</span>
          <span v-if="item.funcionario_nome" class="text-xs text-red-400 ml-2">· {{ item.funcionario_nome }}</span>
        </div>
        <span class="text-[11px] font-semibold text-red-500 whitespace-nowrap shrink-0">
          {{ item.dias_atraso }}d atraso · {{ formatDate(item.data_previsao) }}
        </span>
      </button>
    </div>
  </div>
</template>
