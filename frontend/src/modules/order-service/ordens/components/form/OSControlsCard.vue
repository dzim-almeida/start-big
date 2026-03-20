<script setup lang="ts">
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';

interface Props {
  status: string;
  funcionarioId: number | string | undefined;
  prioridade: string;
  dataPrevisao: string | undefined;
  statusOptions: SelectOption[];
  prioridadeOptions: SelectOption[];
  funcionariosOptions: SelectOption[];
}

defineProps<Props>();

const emit = defineEmits<{
  'update:status': [value: string];
  'update:funcionarioId': [value: string];
  'update:prioridade': [value: string];
  'update:dataPrevisao': [value: string];
}>();
</script>

<template>
  <div class="w-full bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <BaseSelect
        :model-value="status"
        label="Situacao"
        :options="statusOptions"
        @update:model-value="emit('update:status', $event as OrdemServicoStatus)"
      />

      <BaseSelect
        :model-value="funcionarioId"
        label="Tecnico"
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
        @update:model-value="emit('update:prioridade', $event as OrdemServicoPrioridade)"
      />

      <BaseInput
        :model-value="dataPrevisao"
        label="Previsao"
        type="date"
        @update:model-value="emit('update:dataPrevisao', $event as string)"
      />
    </div>
  </div>
</template>
