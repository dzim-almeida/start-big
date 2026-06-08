<script setup lang="ts">
import { ListPlus, BadgeDollarSign, Truck, TicketPercent } from 'lucide-vue-next';
import { formatCurrency } from '@/shared/utils/finance';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import type { SaleUpdate } from '../../schemas/sale.schema';

const props = defineProps<{
  subtotal?: number;
  discount?: number;
  delivery?: number;
  total?: number;
  form?: SaleUpdate;
  isSaving?: boolean;
  readonly?: boolean;
  onSave?: () => void;
}>();
</script>

<template>
  <section class="w-full flex items-center bg-brand-primary/10 border border-brand-primary/20 rounded-lg px-4 py-3 gap-2">
    <!-- Subtotal -->
    <div class="flex-1 flex items-center gap-2 min-w-0">
      <ListPlus :size="15" class="text-brand-action shrink-0" />
      <div class="min-w-0">
        <p class="text-[10px] font-semibold text-zinc-500 uppercase">Subtotal</p>
        <span class="font-bold text-base text-zinc-700 whitespace-nowrap">{{ formatCurrency(subtotal ?? 0) }}</span>
      </div>
    </div>

    <div class="w-px h-8 bg-brand-primary/20 shrink-0" />

    <!-- Desconto -->
    <div class="flex-1 flex items-center gap-2 min-w-0">
      <TicketPercent :size="15" class="text-brand-action shrink-0" />
      <div class="min-w-0 flex-1">
        <p class="text-[10px] font-semibold text-zinc-500 uppercase">Desconto</p>
        <MoneyInput
          v-if="form && !readonly"
          v-model.number="form.desconto"
          :disabled="isSaving"
          class="w-full max-w-28 bg-white/80"
          data-sale-desconto
          @blur="onSave"
          @enter="onSave"
        />
        <span v-else class="font-bold text-base text-zinc-700">{{ formatCurrency(discount ?? 0) }}</span>
      </div>
    </div>

    <div class="w-px h-8 bg-brand-primary/20 shrink-0" />

    <!-- Entrega -->
    <div class="flex-1 flex items-center gap-2 min-w-0">
      <Truck :size="15" class="text-brand-action shrink-0" />
      <div class="min-w-0 flex-1">
        <p class="text-[10px] font-semibold text-zinc-500 uppercase">Entrega</p>
        <MoneyInput
          v-if="form && !readonly"
          v-model.number="form.entrega"
          :disabled="isSaving"
          class="w-full max-w-28 bg-white/80"
          data-sale-entrega
          @blur="onSave"
          @enter="onSave"
        />
        <span v-else class="font-bold text-base text-zinc-700">{{ formatCurrency(delivery ?? 0) }}</span>
      </div>
    </div>

    <div class="w-px h-8 bg-brand-primary/20 shrink-0" />

    <!-- Total -->
    <div class="flex items-center gap-2 shrink-0">
      <BadgeDollarSign :size="18" class="text-brand-primary shrink-0" />
      <div>
        <p class="text-[10px] font-semibold text-zinc-500 uppercase">Total</p>
        <span class="font-bold text-xl text-brand-primary whitespace-nowrap">{{ formatCurrency(total ?? 0) }}</span>
      </div>
    </div>
  </section>
</template>
