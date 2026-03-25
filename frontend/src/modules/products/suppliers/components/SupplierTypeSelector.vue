// ============================================================================
// COMPONENTE: SupplierTypeSelector (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Interface de seleção inicial para o tipo de fornecedor.
// FUNCIONALIDADES: Renderização dinâmica de cards clicáveis com ícones, 
//                  descrições e efeitos visuais de hover/escala para UX.
// ============================================================================
<script setup lang="ts">
import { Package, Truck, Bike } from 'lucide-vue-next';
import type { SupplierTipo } from '../types/fornecedor.types';

const emit = defineEmits<{
  select: [tipo: SupplierTipo];
}>();

const TIPOS = [
  {
    tipo: 'produto' as SupplierTipo,
    icon: Package,
    label: 'Fornecedor de Produtos',
    description: 'Empresas que fornecem produtos para o seu estoque',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200 hover:border-blue-400',
  },
  {
    tipo: 'transportadora' as SupplierTipo,
    icon: Truck,
    label: 'Transportadora',
    description: 'Empresas responsáveis pelo transporte de mercadorias',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200 hover:border-blue-400',
  },
  {
    tipo: 'entregador' as SupplierTipo,
    icon: Bike,
    label: 'Entregador',
    description: 'Profissionais autônomos de entrega (motoboy, ciclista etc.)',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200 hover:border-blue-400',
  },
];
</script>

<template>
  <div>
    <p class="text-sm text-zinc-500 mb-6">
      Selecione o tipo de fornecedor que deseja cadastrar:
    </p>

    <div class="grid grid-cols-1 gap-4">
      <button
        v-for="item in TIPOS"
        :key="item.tipo"
        type="button"
        :class="[
          'group flex items-center gap-4 p-5 rounded-2xl border-2 bg-white transition-all duration-200 text-left cursor-pointer',
          'hover:shadow-md hover:scale-[1.01]',
          item.border,
        ]"
        @click="emit('select', item.tipo)"
      >
        <div
          :class="[
            'flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center',
            item.bg,
            item.color,
          ]"
        >
          <component :is="item.icon" :size="24" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-zinc-800 group-hover:text-zinc-900">
            {{ item.label }}
          </p>
          <p class="text-xs text-zinc-400 mt-0.5">{{ item.description }}</p>
        </div>
        <div class="flex-shrink-0 text-zinc-300 group-hover:text-zinc-500 transition-colors">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="m9 18 6-6-6-6" />
          </svg>
        </div>
      </button>
    </div>
  </div>
</template>
