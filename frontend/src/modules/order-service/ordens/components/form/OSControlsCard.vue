<script setup lang="ts">
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { OsStatusEnumDataType, OsPriorityEnumDataType } from '../../schemas/enums/osEnums.schema';

interface Props {
  status: OsStatusEnumDataType;
  funcionarioId: string;
  prioridade: OsPriorityEnumDataType;
  dataPrevisao: string;
  statusOptions: SelectOption[];
  prioridadeOptions: SelectOption[];
  funcionariosOptions: SelectOption[];
}

defineProps<Props>();

const emit = defineEmits<{
  'update:status': [value: OsStatusEnumDataType];
  'update:funcionarioId': [value: string];
  'update:prioridade': [value: OsPriorityEnumDataType];
  'update:dataPrevisao': [value: string];
}>();
</script>

<template>
  <div class="w-full bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <BaseSelect
        :model-value="status"
        label="Situação"
        :options="statusOptions"
        @update:model-value="emit('update:status', $event as OsStatusEnumDataType)"
      />

      <BaseSelect
        :model-value="funcionarioId"
        label="Técnico"
        :options="funcionariosOptions"
        placeholder="-- Selecione --"
        @update:model-value="emit('update:funcionarioId', $event as string)"
      />
    </div>

    <div class="border-t border-slate-100 my-2"></div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <BaseSelect
        :model-value="prioridade"
        label="Prioridade"
        :options="prioridadeOptions"
        @update:model-value="emit('update:prioridade', $event as OsPriorityEnumDataType)"
      />

      <BaseInput
        :model-value="dataPrevisao"
        label="Previsão"
        type="date"
        @update:model-value="emit('update:dataPrevisao', $event as string)"
      />
    </div>
  </div>
</template>
