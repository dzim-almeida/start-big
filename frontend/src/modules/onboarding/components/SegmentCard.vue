<script setup lang="ts">
/**
 * @component SegmentCard
 * @description Card clicável para seleção de segmento de negócio.
 * Apresenta ícone, label e estado selecionado com animações suaves.
 */

import SegmentIcons from './icons/SegmentIcons.vue';
import type { BusinessSegment } from '../types/onboarding.types';

/* ============================================
   Types
   ============================================ */

/**
 * Tipos de ícones de segmento disponíveis
 */
type SegmentIconType =
  | 'computer'
  | 'wrench'
  | 'store'
  | 'hammer'
  | 'bolt'
  | 'grid'
  | 'building';

/* ============================================
   Props
   ============================================ */

/**
 * Props do componente SegmentCard
 * @property {BusinessSegment} id - Identificador único do segmento
 * @property {string} label - Texto exibido no card
 * @property {SegmentIconType} icon - Ícone do segmento a ser exibido
 * @property {boolean} [selected=false] - Indica se o card está selecionado
 */
interface Props {
  id: BusinessSegment;
  label: string;
  icon: SegmentIconType;
  selected?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  selected: false,
});

/* ============================================
   Emits
   ============================================ */

/**
 * Eventos emitidos pelo componente
 * @event select - Emitido quando o card é clicado, passa o id do segmento
 */
const emit = defineEmits<{
  select: [id: BusinessSegment];
}>();

/* ============================================
   Methods
   ============================================ */

/**
 * Handler de clique no card
 * Emite o evento de seleção com o id do segmento
 */
function handleClick(): void {
  emit('select', props.id);
}
</script>

<template>
  <button
    type="button"
    @click="handleClick"
    :class="[
      'group relative w-full p-6 rounded-xl border-2 transition-all duration-300 ease-out',
      'flex flex-col items-center gap-3 cursor-pointer',
      'hover:shadow-lg hover:-translate-y-1',
      'focus:outline-none focus:ring-2 focus:ring-brand-primary focus:ring-offset-2',
      selected
        ? 'border-brand-primary bg-blue-50 shadow-md'
        : 'border-gray-200 bg-white hover:border-brand-secondary hover:bg-gray-50',
    ]"
  >
    <!-- Indicador de seleção -->
    <div
      :class="[
        'absolute top-3 right-3 w-5 h-5 rounded-full border-2 transition-all duration-300',
        'flex items-center justify-center',
        selected
          ? 'border-brand-primary bg-brand-primary'
          : 'border-gray-300 bg-white group-hover:border-brand-secondary',
      ]"
    >
      <svg
        v-if="selected"
        class="w-3 h-3 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="3"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    </div>

    <!-- Ícone do segmento -->
    <div
      :class="[
        'p-3 rounded-xl transition-all duration-300',
        selected ? 'bg-white shadow-sm' : 'bg-gray-50 group-hover:bg-white',
      ]"
    >
      <SegmentIcons :icon="icon" size="lg" />
    </div>

    <!-- Label -->
    <span
      :class="[
        'text-sm font-semibold transition-colors duration-300 text-center',
        selected ? 'text-brand-primary' : 'text-gray-700 group-hover:text-brand-action',
      ]"
    >
      {{ label }}
    </span>
  </button>
</template>
