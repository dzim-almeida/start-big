<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '@/shared/stores/auth.store';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { OsStatusEnumDataType, OsPriorityEnumDataType } from '../../schemas/enums/osEnums.schema';

const props = defineProps<{
  status?: OsStatusEnumDataType;
  funcionarioId?: string | number;
  prioridade?: OsPriorityEnumDataType;
  dataPrevisao?: string;
  statusOptions: SelectOption[];
  prioridadeOptions: SelectOption[];
  funcionariosOptions: SelectOption[];
  canSelectTecnico?: boolean;
  isCreateMode?: boolean;
  isLocked?: boolean;
  errors?: Record<string, string | string[] | undefined>;
}>();

const emit = defineEmits<{
  'update:status': [value: OsStatusEnumDataType];
  'update:funcionarioId': [value: string];
  'update:prioridade': [value: OsPriorityEnumDataType];
  'update:dataPrevisao': [value: string];
}>();

const authStore = useAuthStore();

const localStatus = computed({
  get: () => String(props.status || ''),
  set: (val) => emit('update:status', val as OsStatusEnumDataType)
});

const localFuncionarioId = computed({
  get: () => String(props.funcionarioId || ''),
  set: (val) => emit('update:funcionarioId', val)
});

const localPrioridade = computed({
  get: () => String(props.prioridade || ''),
  set: (val) => emit('update:prioridade', val as OsPriorityEnumDataType)
});

const localDataPrevisao = computed({
  get: () => props.dataPrevisao || '',
  set: (val) => emit('update:dataPrevisao', val)
});
</script>

<template>
  <div class="w-full bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden text-sm">
    <div class="grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-slate-100">
      
      <!-- Situação -->
      <div class="flex flex-col px-4 py-2 hover:bg-slate-50 transition-colors group">
        <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Situação</span>
        <select
          v-model="localStatus"
          :disabled="isLocked"
          class="bg-transparent border-none text-left font-semibold text-slate-700 focus:ring-0 outline-none p-0 -ml-1 w-full disabled:cursor-not-allowed disabled:opacity-70"
          :class="isLocked ? '' : 'cursor-pointer'"
        >
          <option v-for="opt in statusOptions" :key="opt.value" :value="String(opt.value)">{{ opt.label }}</option>
        </select>
      </div>

      <!-- Técnico -->
      <div class="flex flex-col px-4 py-2 hover:bg-slate-50 transition-colors">
        <span class="text-[10px] font-bold uppercase tracking-wider mb-0.5" :class="errors?.funcionario_id ? 'text-red-500' : 'text-slate-400'">Técnico</span>
        <select
          v-if="canSelectTecnico && !isLocked"
          v-model="localFuncionarioId"
          class="bg-transparent border-none text-left font-semibold text-slate-700 focus:ring-0 cursor-pointer outline-none p-0 -ml-1 w-full truncate"
        >
          <option value="" disabled>-- Selecione --</option>
          <option v-for="opt in funcionariosOptions" :key="opt.value" :value="String(opt.value)">{{ opt.label }}</option>
        </select>
        <span v-else class="font-semibold text-slate-700 mt-0.5 truncate">
          {{ funcionariosOptions.find(opt => String(opt.value) === localFuncionarioId)?.label || authStore.userData?.nome || '--' }}
        </span>
      </div>

      <!-- Prioridade -->
      <div class="flex flex-col px-4 py-2 hover:bg-slate-50 transition-colors group">
        <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Prioridade</span>
        <select
          v-model="localPrioridade"
          :disabled="isLocked"
          class="bg-transparent border-none text-left font-semibold text-slate-700 focus:ring-0 outline-none p-0 -ml-1 w-full disabled:cursor-not-allowed disabled:opacity-70"
          :class="isLocked ? '' : 'cursor-pointer'"
        >
          <option v-for="opt in prioridadeOptions" :key="opt.value" :value="String(opt.value)">{{ opt.label }}</option>
        </select>
      </div>

      <!-- Previsão -->
      <div class="flex flex-col px-4 py-2 hover:bg-slate-50 transition-colors group">
        <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Previsão</span>
        <input
          type="date"
          v-model="localDataPrevisao"
          :disabled="isLocked"
          class="bg-transparent border-none text-left font-semibold text-slate-700 focus:ring-0 outline-none p-0 w-full disabled:cursor-not-allowed disabled:opacity-70"
          :class="isLocked ? '' : 'cursor-pointer'"
        />
      </div>

    </div>
  </div>
</template>
