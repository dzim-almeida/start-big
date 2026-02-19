<script setup lang="ts">
/**
 * OSControlsCard.vue
 * Card de controles da OS (status, tecnico, prioridade, previsao)
 */
import type { OrdemServicoStatus, OrdemServicoPrioridade } from '../../types/ordemServico.types';

interface StatusOption {
  value: OrdemServicoStatus;
  label: string;
  color: string;
}

interface PrioridadeOption {
  value: OrdemServicoPrioridade;
  label: string;
  color: string;
}

interface FuncionarioOption {
  value: string;
  label: string;
}

interface Props {
  status: OrdemServicoStatus;
  funcionarioId: string;
  prioridade: OrdemServicoPrioridade;
  dataPrevisao: string;
  statusOptions: readonly StatusOption[];
  prioridadeOptions: readonly PrioridadeOption[];
  funcionariosOptions: FuncionarioOption[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:status': [value: OrdemServicoStatus];
  'update:funcionarioId': [value: string];
  'update:prioridade': [value: OrdemServicoPrioridade];
  'update:dataPrevisao': [value: string];
}>();
</script>

<template>
  <div class="w-full bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
    <!-- Linha 1: Status e Tecnico -->
    <div class="grid grid-cols-2 gap-4">
      <!-- Status -->
      <div>
        <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Situacao</label>
        <div class="relative">
          <select
            :value="status"
            class="w-full text-xs font-bold text-slate-800 bg-slate-50 py-1.5 px-2 border border-slate-200 rounded focus:border-brand-primary-light0 focus:outline-none"
            @change="emit('update:status', ($event.target as HTMLSelectElement).value as OrdemServicoStatus)"
          >
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- Tecnico -->
      <div>
        <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Tecnico</label>
        <div class="relative">
          <select
            :value="funcionarioId"
            class="w-full text-xs font-bold text-slate-800 bg-slate-50 py-1.5 px-2 border border-slate-200 rounded focus:border-brand-primary-light0 focus:outline-none"
            @change="emit('update:funcionarioId', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">-- Selecione --</option>
            <option v-for="opt in funcionariosOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <div class="border-t border-slate-100 my-2"></div>

    <!-- Linha 2: Prioridade e Previsao -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Prioridade</label>
        <div class="relative">
          <select
            :value="prioridade"
            class="w-full text-xs font-bold text-slate-800 bg-slate-50 py-1.5 px-2 border border-slate-200 rounded focus:border-brand-primary-light0 focus:outline-none"
            @change="emit('update:prioridade', ($event.target as HTMLSelectElement).value as OrdemServicoPrioridade)"
          >
            <option v-for="opt in prioridadeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>

      <div>
        <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Previsao</label>
        <input
          :value="dataPrevisao"
          type="date"
          class="w-full text-xs font-semibold text-slate-700 bg-slate-50 py-1.5 px-2 border border-slate-200 rounded focus:border-brand-primary-light0 focus:outline-none"
          @input="emit('update:dataPrevisao', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
  </div>
</template>
