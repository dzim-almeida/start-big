<script setup lang="ts">
import { User2, Building2, UserX, RefreshCw } from 'lucide-vue-next';
import { getInitials } from '@/shared/utils/string.utils';
import type { CustomerSimpleRead } from '../../schemas/customers.schema';

const props = defineProps<{
  customer: CustomerSimpleRead[number] | undefined | null;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  changeCliente: [];
}>();

function getNome(c: typeof props.customer) {
  if (!c) return '';
  return c.tipo === 'PF' ? c.nome : c.razao_social;
}

function getDoc(c: typeof props.customer) {
  if (!c) return '';
  return c.tipo === 'PF' ? c.cpf : c.cnpj;
}
</script>

<template>
  <div class="rounded-xl border border-zinc-200 bg-white p-3">
    <!-- Com cliente -->
    <div v-if="customer" class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-full bg-brand-primary/10 flex items-center justify-center shrink-0">
        <span class="text-[11px] font-bold text-brand-primary">{{ getInitials(getNome(customer)) }}</span>
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-semibold text-zinc-900 truncate">{{ getNome(customer) }}</p>
        <p class="text-xs text-zinc-400 truncate">{{ getDoc(customer) || 'Sem documento' }}</p>
      </div>
      <button
        v-if="!readonly"
        type="button"
        class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-brand-primary hover:bg-brand-primary/10 rounded-md transition-colors cursor-pointer shrink-0"
        @click="emit('changeCliente')"
      >
        <RefreshCw :size="11" />
        Trocar
      </button>
    </div>

    <!-- Sem cliente -->
    <div v-else class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-full bg-zinc-100 flex items-center justify-center shrink-0">
        <UserX :size="16" class="text-zinc-400" />
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-zinc-400">Nenhum cliente</p>
        <p class="text-xs text-zinc-300">Venda sem identificação</p>
      </div>
      <button
        v-if="!readonly"
        type="button"
        class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-brand-primary hover:bg-brand-primary/10 rounded-md transition-colors cursor-pointer shrink-0"
        @click="emit('changeCliente')"
      >
        <component :is="User2" :size="11" />
        Selecionar
      </button>
    </div>
  </div>
</template>
