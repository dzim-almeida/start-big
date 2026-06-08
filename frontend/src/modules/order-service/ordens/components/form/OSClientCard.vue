<script setup lang="ts">
import { computed } from 'vue';
import {
  Building2,
  User,
  Home,
  Phone,
  RefreshCw,
  Pencil,
  History,
} from 'lucide-vue-next';

import type { CustomerUnionReadSchemaDataType } from '../../schemas/relationship/customer/customer.schema';
import { useCustomerModal } from '@/modules/customers/composables/modal/useCustomerModal';
import type { CustomerUnionReadSchemaDataType as SharedCustomerType } from '@/shared/schemas/customer/customer.schema';

import { maskPhoneNumber } from '@/shared/utils/mask.utils';

interface Props {
  cliente?: CustomerUnionReadSchemaDataType | null;
  isEditMode?: boolean;
  isLocked?: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  changeCliente: [];
  updateCliente: [cliente: CustomerUnionReadSchemaDataType];
  openHistorico: [];
}>();

const { openEditModalWithCallback } = useCustomerModal();

function handleEditCliente() {
  if (!props.cliente) return;
  openEditModalWithCallback(props.cliente as SharedCustomerType, (updated) => {
    emit('updateCliente', updated as CustomerUnionReadSchemaDataType);
  });
}

const isClientePJ = computed(() => {
  const c = props.cliente as { tipo?: string } | null | undefined;
  return c?.tipo === 'PJ';
});

const clienteNome = computed(() => {
  if (!props.cliente) return 'Selecione um cliente';
  const c = props.cliente as { tipo: string; nome?: string; nome_fantasia?: string; razao_social?: string };
  if (c.tipo === 'PF') return c.nome || '-';
  return c.nome_fantasia || c.razao_social || '-';
});

const formattedAddress = computed(() => {
  if (!props.cliente?.endereco) return 'Endereço não cadastrado';

  // Defensivo: endereco pode vir como array (fallback sem preprocess) ou objeto
  const raw = props.cliente.endereco;
  const end = Array.isArray(raw) ? raw[0] : raw;

  if (!end || typeof end !== 'object') return 'Endereço não cadastrado';

  const { logradouro, numero, bairro, cidade, estado } = end as {
    logradouro?: string;
    numero?: string;
    bairro?: string;
    cidade?: string;
    estado?: string;
  };

  if (!logradouro) return 'Endereço não cadastrado';
  return `${logradouro}, ${numero ?? 'S/N'} - ${bairro}, ${cidade}/${estado}`;
});

const formattedPhone = computed(() => {
  return maskPhoneNumber(props.cliente?.celular) || maskPhoneNumber(props.cliente?.telefone) || 'Contato não cadastrado';
});

const canChangeCliente = computed(() => {
  return !props.isEditMode && !props.isLocked;
});
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:border-brand-primary/30 transition-colors group relative">
    <div class="bg-slate-50 px-4 py-2 border-b border-slate-100 flex justify-between items-center">
      <div class="flex items-center gap-2">
        <Building2 v-if="isClientePJ" :size="14" class="text-brand-primary" />
        <User v-else :size="14" class="text-brand-primary" />
        <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">
          DADOS DO CLIENTE
        </span>
      </div>
      <div class="flex items-center gap-1">
        <button
          v-if="props.cliente"
          type="button"
          class="text-[10px] font-bold text-brand-primary hover:text-brand-primary/80 flex items-center gap-1 px-2 py-0.5 rounded-full hover:bg-brand-primary-light transition-colors"
          @click="emit('openHistorico')"
        >
          <History :size="10" /> HISTÓRICO
        </button>
        <button
          v-if="props.cliente && props.isEditMode"
          type="button"
          class="text-[10px] font-bold text-brand-primary hover:text-brand-primary/80 flex items-center gap-1 px-2 py-0.5 rounded-full hover:bg-brand-primary-light transition-colors"
          @click="handleEditCliente"
        >
          <Pencil :size="10" /> EDITAR
        </button>
        <button
          v-if="canChangeCliente"
          type="button"
          class="text-[10px] font-bold text-brand-primary hover:text-brand-primary/80 flex items-center gap-1 px-2 py-0.5 rounded-full hover:bg-brand-primary-light transition-colors"
          @click="emit('changeCliente')"
        >
          <RefreshCw :size="10" /> TROCAR
        </button>
      </div>
    </div>

    <div class="p-4 pt-3">
      <div class="flex items-center gap-2 mb-3">
        <span class="text-base font-bold text-slate-900 leading-tight">{{ clienteNome }}</span>
      </div>

      <div class="space-y-2">
        <div class="flex items-start gap-2.5">
          <Home :size="14" class="text-slate-400 mt-0.5 shrink-0" />
          <span class="text-xs text-slate-600 font-medium leading-snug">{{ formattedAddress }}</span>
        </div>
        <div class="flex items-center gap-2.5">
          <Phone :size="14" class="text-slate-400 shrink-0" />
          <span class="text-xs text-slate-600 font-medium">{{ formattedPhone }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
