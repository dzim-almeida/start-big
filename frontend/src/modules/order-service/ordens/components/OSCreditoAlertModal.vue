<script setup lang="ts">
import { Wallet, ArrowRight } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { formatCurrency } from '@/shared/utils/finance';

interface Props {
  isOpen: boolean;
  valorCredito: number;
  nomeCliente?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  usar: [];
  fechar: [];
}>();
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Crédito disponível"
    size="sm"
    @close="emit('fechar')"
  >
    <div class="flex flex-col items-center gap-5 py-2">
      <div class="p-4 bg-emerald-50 rounded-full">
        <Wallet :size="32" class="text-emerald-500" />
      </div>

      <div class="text-center space-y-1">
        <p class="text-sm font-semibold text-zinc-800">
          {{ props.nomeCliente ? props.nomeCliente : 'Este cliente' }} possui
          <span class="text-emerald-600">{{ formatCurrency(props.valorCredito) }}</span>
          em crédito
        </p>
        <p class="text-xs text-zinc-500">Deseja usar o crédito como entrada nesta OS?</p>
      </div>

      <div class="grid grid-cols-2 gap-3 w-full">
        <button
          type="button"
          class="flex flex-col items-center gap-2 p-3.5 rounded-xl border-2 border-emerald-400 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-all"
          @click="emit('usar')"
        >
          <Wallet :size="20" />
          <span class="text-xs font-semibold text-center leading-tight">Usar crédito</span>
        </button>
        <button
          type="button"
          class="flex flex-col items-center gap-2 p-3.5 rounded-xl border-2 border-zinc-200 bg-zinc-50 text-zinc-500 hover:bg-zinc-100 transition-all"
          @click="emit('fechar')"
        >
          <ArrowRight :size="20" />
          <span class="text-xs font-semibold text-center leading-tight">Pular por agora</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
