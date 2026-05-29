<script setup lang="ts">
import { computed } from 'vue';

import { TicketPercent, Truck, UserRound, CalendarDays, Settings } from 'lucide-vue-next';

import { useSaleDetailsForm } from '../../composables/flows/useSaleDetailsForm';
import { STATUS_COLORS, SALE_FILTERS } from '../../constants';

import BaseInfoCard from '@/shared/components/layout/StatsCard/BaseInfoCard.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

import { SaleRead } from '../../schemas/sale.schema';

const props = defineProps<{
  sale: SaleRead | undefined;
  readonly: boolean;
}>();

const saleRef = computed(() => props.sale);
const { form, isSaving, saveNow } = useSaleDetailsForm(saleRef);

const saleDisplay = computed(() => {
  if (!props.sale) return '...';

  const prefix = props.sale.status === 'ORCAMENTO' ? 'ORÇAMENTO' : 'VENDA';   

  if (props.sale.numero_venda) {

    return `${prefix} #${String(props.sale.numero_venda).padStart(6, '0')}`;
  }
  return `${prefix} #${String(props.sale.id).padStart(6, '0')}`;
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
  <BaseInfoCard :icon="Settings" title="Dados da venda">
    <div class="px-4 py-3 flex flex-col gap-3">
      <!-- Número da Venda + Status -->
      <div class="flex items-center gap-2">
        <h2 class="font-poppins font-bold text-sm text-zinc-800 underline underline-offset-2">
          {{ saleDisplay }}
        </h2>
        <span
          v-if="sale?.status"
          :class="[
            'px-2.5 py-0.5 text-[10px] font-semibold rounded-full border',
            STATUS_COLORS[sale.status].text,
            STATUS_COLORS[sale.status].bg,
          ]"
        >
          {{ SALE_FILTERS[sale.status].label }}
        </span>
      </div>

      <!-- Funcionário Responsável -->
      <div class="flex flex-col gap-1">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Funcionário Responsável</h2>
        <div class="flex items-center gap-2">
          <UserRound :size="18" class="text-zinc-500 shrink-0" />
          <div class="flex flex-col">
            <span class="font-poppins text-sm text-zinc-800">{{ sale?.funcionario?.nome ?? '—' }}</span>
            <span
              v-if="sale?.funcionario?.cargo?.nome"
              class="font-poppins text-[10px] font-bold text-blue-600 uppercase tracking-wide"
            >
              {{ sale.funcionario.cargo.nome }}
            </span>
          </div>
        </div>
      </div>

      <!-- Criada em -->
      <div class="flex flex-col gap-1">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Criada em</h2>
        <div class="flex items-center gap-2">
          <CalendarDays :size="18" class="text-zinc-500 shrink-0" />
          <p class="font-poppins text-sm">
            {{ createdAt }}
          </p>
        </div>
      </div>

      <!-- Entrega -->
      <div class="flex flex-col gap-1">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Entrega</h2>
        <div class="flex gap-2 items-center">
          <Truck :size="18" class="text-zinc-500 shrink-0" />
          <MoneyInput v-model.number="form.entrega" :disabled="isSaving || readonly" @blur="saveNow" @enter="saveNow" class="w-auto" />
        </div>
      </div>

      <!-- Desconto -->
      <div class="flex flex-col gap-1">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Desconto</h2>
        <div class="flex gap-2 items-center">
          <TicketPercent :size="18" class="text-zinc-500 shrink-0" />
          <MoneyInput v-model.number="form.desconto" :disabled="isSaving || readonly" @blur="saveNow" @enter="saveNow" class="w-auto" />
        </div>
      </div>

      <!-- Observação -->
      <div class="flex flex-col gap-1">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Observação</h2>
        <BaseTextarea v-model="form.observacao" :disabled="isSaving || readonly" placeholder="Adicione uma observação sobre essa venda" class="w-full" />
      </div>
    </div>
  </BaseInfoCard>
</template>
