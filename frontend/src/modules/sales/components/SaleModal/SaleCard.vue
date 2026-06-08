<script setup lang="ts">
import { computed } from 'vue';
import { UserRound, CalendarDays } from 'lucide-vue-next';
import { STATUS_COLORS, SALE_FILTERS } from '../../constants';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import type { SaleRead, SaleUpdate } from '../../schemas/sale.schema';

const props = defineProps<{
  sale: SaleRead | undefined;
  readonly: boolean;
  form: SaleUpdate;
  isSaving: boolean;
  onSave: () => void;
}>();

const saleDisplay = computed(() => {
  if (!props.sale) return '...';
  return `VENDA #${String(props.sale.id).padStart(6, '0')}`;
});

const createdAt = computed(() => {
  if (!props.sale?.criado_em) return null;
  const date = new Date(props.sale.criado_em).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
  const time = props.sale.criado_em.split('T')[1];
  return `${date} às ${time}`;
});
</script>

<template>
  <div class="rounded-xl border border-zinc-200 bg-white p-3 flex flex-col gap-3">
    <!-- Número + Status -->
    <div class="flex items-center justify-between">
      <span class="font-bold text-sm text-zinc-800">{{ saleDisplay }}</span>
      <span
        v-if="sale?.status"
        :class="[
          'px-2 py-0.5 text-[10px] font-semibold rounded-full border',
          STATUS_COLORS[sale.status].text,
          STATUS_COLORS[sale.status].bg,
        ]"
      >
        {{ SALE_FILTERS[sale.status].label }}
      </span>
    </div>

    <!-- Funcionário + Data lado a lado -->
    <div class="grid grid-cols-2 gap-2">
      <div class="flex flex-col gap-0.5">
        <span class="text-[10px] font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-1">
          <UserRound :size="10" /> Funcionário
        </span>
        <span class="text-xs font-medium text-zinc-700 truncate">{{ sale?.funcionario?.nome ?? '—' }}</span>
        <span v-if="sale?.funcionario?.cargo?.nome" class="text-[10px] text-blue-500 font-semibold truncate">
          {{ sale.funcionario.cargo.nome }}
        </span>
      </div>
      <div class="flex flex-col gap-0.5">
        <span class="text-[10px] font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-1">
          <CalendarDays :size="10" /> Criada em
        </span>
        <span class="text-xs font-medium text-zinc-700">{{ createdAt ?? '—' }}</span>
      </div>
    </div>

    <div class="border-t border-zinc-100" />

    <!-- Observação -->
    <div class="flex flex-col gap-1">
      <span class="text-[10px] font-semibold text-zinc-400 uppercase tracking-wide">Observação</span>
      <BaseTextarea
        v-model="form.observacao"
        :disabled="isSaving || readonly"
        placeholder="Adicione uma observação..."
        :rows="2"
        class="w-full"
        @blur="onSave"
      />
    </div>

    <!-- Observação Interna -->
    <div class="flex flex-col gap-1">
      <span class="text-[10px] font-semibold text-zinc-400 uppercase tracking-wide">Obs. Interna</span>
      <BaseTextarea
        v-model="form.observacao_interna"
        :disabled="isSaving || readonly"
        placeholder="Nota interna (não impressa no comprovante)..."
        :rows="2"
        class="w-full"
        @blur="onSave"
      />
    </div>
  </div>
</template>
