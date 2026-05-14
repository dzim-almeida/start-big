<script setup lang="ts">
import { Ticket, TicketPercent, Truck, Pen } from 'lucide-vue-next';

import { useSaleDetailsForm } from '../../composables/useSaleDetailsForm';

import BaseInfoCard from '@/shared/components/layout/StatsCard/BaseInfoCard.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

import { SaleRead } from '../../schemas/sale.schema';

const props = defineProps<{
  sale: SaleRead | undefined;
  readonly: boolean;
}>();

const { form, isSaving, saveNow } = useSaleDetailsForm(props.sale);

</script>
<template>
  <BaseInfoCard :icon="Ticket" title="Dados da venda">
    <div class="px-4 py-3 flex flex-col gap-2">
      <div>
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Criada em</h2>
        <p class="font-poppins text-sm">
          {{ sale?.criado_em[0] }} às {{ sale?.criado_em[1] }}
        </p>
      </div>
      <div class="flex flex-col gap-2">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Desconto</h2>
        <div class="flex gap-4 items-center">
          <TicketPercent :size="20" />
          <MoneyInput v-model.number="form.desconto" :disabled="isSaving || readonly" @blur="saveNow" class="w-auto" />
        </div>
      </div>
      <div class="flex flex-col gap-2">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Entrega</h2>
        <div class="flex gap-4 items-center">
          <Truck :size="20" />
          <MoneyInput v-model.number="form.entrega" :disabled="isSaving || readonly" @blur="saveNow" class="w-auto" />
        </div>
      </div>
      <div class="flex flex-col gap-2">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Observações</h2>
        <div class="flex gap-4 items-center">
          <Pen :size="20" />
          <BaseTextarea v-model="form.observacao" :disabled="isSaving || readonly" placeholder="Adicione informações sobre a venda" class="w-full" />
        </div>
      </div>
    </div>
  </BaseInfoCard>
</template>
