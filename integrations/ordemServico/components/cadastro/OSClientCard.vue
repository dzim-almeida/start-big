<script setup lang="ts">
/**
 * OSClientCard.vue
 * Componente para exibir dados do cliente na OS
 */
import { computed } from 'vue';
import {
  Building2,
  User,
  Home,
  Phone,
  Calendar,
  CheckCircle2,
  RefreshCw,
} from 'lucide-vue-next';

import type { ClienteResumo, OrdemServicoStatus } from '../../types/ordemServico.types';
import type { Cliente } from '@/modules/clientes/types/clientes.types';
import { getStatusLabel, getStatusColor } from '../../utils';

interface Props {
  cliente?: Cliente | ClienteResumo | null;
  status?: OrdemServicoStatus | null;
  dataCriacao?: string | Date;
  dataFinalizacao?: string | Date;
  isEditMode?: boolean;
  isFinalizada?: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  changeCliente: [];
}>();

const isClientePJ = computed(() => props.cliente?.tipo === 'PJ');

const clienteNome = computed(() => {
  if (!props.cliente) return 'Selecione um cliente';

  if (props.cliente.tipo === 'PF') {
    return props.cliente.nome || '-';
  }

  // Para PJ, tenta nome_fantasia primeiro, depois razao_social
  const pj = props.cliente as ClienteResumo;
  return pj.nome_fantasia || pj.razao_social || '-';
});

const formattedAddress = computed(() => {
  // Verifica se e um Cliente completo com endereco
  const clienteCompleto = props.cliente as Cliente | undefined;

  if (clienteCompleto?.endereco?.length) {
    const end = clienteCompleto.endereco[0];
    return `${end.logradouro}, ${end.numero} - ${end.bairro}, ${end.cidade}/${end.estado}`;
  }

  if (props.cliente) {
    return 'Endereco disponivel no cadastro do cliente';
  }

  return 'Endereco nao cadastrado';
});

const formattedPhone = computed(() => {
  return props.cliente?.celular || props.cliente?.telefone || 'Telefone nao informado';
});

const formattedDataEntrada = computed(() => {
  if (!props.dataCriacao) return '-';
  const date = typeof props.dataCriacao === 'string'
    ? new Date(props.dataCriacao)
    : props.dataCriacao;
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
});

const formattedDataSaida = computed(() => {
  if (!props.dataFinalizacao) return '-';
  const date = typeof props.dataFinalizacao === 'string'
    ? new Date(props.dataFinalizacao)
    : props.dataFinalizacao;
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
});

const statusLabel = computed(() => {
  if (!props.status) return 'Nova OS';
  return getStatusLabel(props.status);
});

const statusColorClass = computed(() => {
  const status = props.status || 'ABERTA';
  const color = getStatusColor(status);

  const map: Record<string, string> = {
    blue: 'bg-brand-primary-light text-brand-primary border-brand-primary/20',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-zinc-50 text-zinc-700 border-zinc-200',
  };

  return map[color] || map.gray;
});

const canChangeCliente = computed(() => {
  return !props.isEditMode && !props.isFinalizada;
});

function handleChangeCliente() {
  emit('changeCliente');
}
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:border-brand-primary/30 transition-colors group relative">
    <!-- Header Card -->
    <div class="bg-slate-50 px-4 py-2 border-b border-slate-100 flex justify-between items-center">
      <div class="flex items-center gap-2">
        <Building2 v-if="isClientePJ" :size="14" class="text-orange-600" />
        <User v-else :size="14" class="text-brand-primary" />
        <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">
          DADOS DO CLIENTE
        </span>
      </div>

      <button
        v-if="canChangeCliente"
        type="button"
        class="text-[10px] font-bold text-brand-primary hover:text-brand-primary/80 flex items-center gap-1 px-2 py-0.5 rounded-full hover:bg-brand-primary-light transition-colors"
        @click="handleChangeCliente"
      >
        <RefreshCw :size="10" /> TROCAR
      </button>
    </div>

    <div class="p-4 pt-3">
      <!-- Nome e Status -->
      <div class="flex items-center gap-2 mb-3">
        <span class="text-base font-bold text-slate-900 leading-tight">
          {{ clienteNome }}
        </span>
        <span
          v-if="status"
          :class="['ml-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border', statusColorClass]"
        >
          {{ statusLabel }}
        </span>
      </div>

      <!-- Detalhes -->
      <div class="space-y-2">
        <div class="flex items-start gap-2.5">
          <Home :size="14" class="text-slate-400 mt-0.5 shrink-0" />
          <span class="text-xs text-slate-600 font-medium leading-snug">
            {{ formattedAddress }}
          </span>
        </div>
        <div class="flex items-center gap-2.5">
          <Phone :size="14" class="text-slate-400 shrink-0" />
          <span class="text-xs text-slate-600 font-medium">
            {{ formattedPhone }}
          </span>
        </div>
      </div>

      <!-- Datas -->
      <div class="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2">
        <div class="flex flex-col">
          <span class="text-[10px] text-slate-400 font-bold uppercase">Entrada</span>
          <span class="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
            <Calendar :size="12" class="text-slate-400" />
            {{ formattedDataEntrada }}
          </span>
        </div>

        <div v-if="formattedDataSaida !== '-'" class="flex flex-col">
          <span class="text-[10px] text-slate-400 font-bold uppercase">Saida/Finalizacao</span>
          <span class="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
            <CheckCircle2 :size="12" class="text-emerald-500" />
            {{ formattedDataSaida }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
