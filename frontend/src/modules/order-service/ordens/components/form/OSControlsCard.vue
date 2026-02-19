<script setup lang="ts">
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { OrdemServicoStatus, OrdemServicoPrioridade } from '../../types/ordemServico.types';

interface Props {
  status: OrdemServicoStatus;
  funcionarioId: string;
  prioridade: OrdemServicoPrioridade;
  dataPrevisao: string;
  statusOptions: SelectOption[];
  prioridadeOptions: SelectOption[];
  funcionariosOptions: SelectOption[];
}

defineProps<Props>();

const emit = defineEmits<{
  'update:status': [value: OrdemServicoStatus];
  'update:funcionarioId': [value: string];
  'update:prioridade': [value: OrdemServicoPrioridade];
  'update:dataPrevisao': [value: string];
}>();
</script>

<template>
  <div class="w-full bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
    <div class="grid grid-cols-2 gap-4">
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

    <div class="grid grid-cols-2 gap-4">
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
