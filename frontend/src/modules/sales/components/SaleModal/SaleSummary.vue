<script setup lang="ts">
import { ListPlus, TicketPercent, BadgeDollarSign, Truck } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';

defineProps<{
  subtotal?: number;
  discount?: number;
  delivery?: number;
  total?: number;
}>()
</script>

<template>
    <section class="mt-auto py-5 w-full flex items-center justify-between bg-brand-primary/10 border border-brand-primary/20 rounded-lg shadow-sm overflow-hidden">
        <div class="px-10 flex-1 flex justify-between gap-2 min-w-1/2">
            <div class="flex gap-4 items-center">
                <div class="w-12 h-12 sm:w-10 sm:h-10 bg-white rounded-full flex items-center justify-center">
                    <ListPlus :size="20" class="text-brand-action" />
                </div>
                <div class="flex flex-col gap-1">
                    <p class="font-semibold text-xs sm:text-[10px] text-mid-gray uppercase">Subtotal</p>
                    <span class="font-bold text-xl sm:text-md text-zinc-700">{{ formatCurrency(subtotal ? subtotal : 0) }}</span>
                </div>
            </div>
            <div class="flex gap-4 items-center">
                <div class="w-12 h-12 sm:w-10 sm:h-10 bg-white rounded-full flex items-center justify-center">
                    <TicketPercent :size="20" class="text-brand-action" />
                </div>
                <div class="flex flex-col gap-1">
                    <p class="font-semibold text-xs sm:text-[10px] text-mid-gray uppercase">Desconto</p>
                    <span class="font-bold text-xl sm:text-md text-zinc-700">{{ formatCurrency(discount ? discount : 0) }}</span>
                </div>
            </div>
            <div class="flex gap-4 items-center">
                <div class="w-12 h-12 sm:w-10 sm:h-10 bg-white rounded-full flex items-center justify-center">
                    <Truck :size="20" class="text-brand-action" />
                </div>
                <div class="flex flex-col gap-1">
                    <p class="font-semibold text-xs sm:text-[10px] text-mid-gray uppercase">Entrega</p>
                    <span class="font-bold text-xl sm:text-md text-zinc-700">{{ formatCurrency(delivery ? delivery : 0) }}</span>
                </div>
            </div>
            <div class="flex gap-4 items-center">
                <div class="w-15 h-15 sm:w-12 sm:h-12 bg-white rounded-full flex items-center justify-center">
                    <BadgeDollarSign :size="25" class="text-brand-primary" />
                </div>
                <div class="flex flex-col gap-1">
                    <p class="font-semibold text-sm text-mid-gray uppercase">Total</p>
                    <span class="font-bold text-2xl sm:text-xl text-brand-primary">{{ formatCurrency(total ? total : 0) }}</span>
                </div>
            </div>
        </div>
    </section>
</template>