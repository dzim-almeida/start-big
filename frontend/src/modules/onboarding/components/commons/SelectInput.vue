<script setup lang="ts">
/**
 * @component SelectInput
 * @description Componente de select customizado com ícone de seta.
 * Emite eventos de seleção para o componente pai.
 */

import Icons from '../icons/Icons.vue';

/* ============================================
   Types
   ============================================ */

/**
 * Interface para opções do select
 * @property {string} label - Texto exibido na opção
 * @property {string} value - Valor da opção
 */
interface SelectOption {
  label: string;
  value: string;
}

/* ============================================
   Props
   ============================================ */

/**
 * Props do componente SelectInput
 * @property {SelectOption[]} options - Lista de opções disponíveis
 */
interface Props {
  options: SelectOption[];
}

defineProps<Props>();

/* ============================================
   Emits
   ============================================ */

/**
 * Eventos emitidos pelo componente
 * @event select - Emitido quando uma opção é selecionada
 */
const emit = defineEmits<{
  select: [value: string];
}>();

/* ============================================
   Methods
   ============================================ */

/**
 * Handler para mudança de seleção
 * @param {string} value - Valor da opção selecionada
 */
function changeSelect(value: string): void {
  emit('select', value);
}
</script>

<template>
  <div class="relative h-fit">
    <select
      :value="options[0].value"
      @change="changeSelect(($event.target as HTMLSelectElement).value)"
      class="h-full px-3 py-2 border border-gray-300 rounded-md bg-white text-sm text-gray-700 focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary cursor-pointer appearance-none pr-8"
    >
      <option v-for="(option, index) in options" :key="index" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <div class="absolute right-2 top-1/2 -translate-y-1/2">
      <Icons icon="select" />
    </div>
  </div>
</template>
