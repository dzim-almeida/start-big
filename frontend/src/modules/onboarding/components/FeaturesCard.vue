<script setup lang="ts">
/**
 * @component FeaturesCard
 * @description Card reutilizável para exibir funcionalidades/recursos do sistema.
 * Apresenta um ícone via slot, título e descrição com animação de hover.
 */

/* ============================================
   Props
   ============================================ */

/**
 * Props do componente FeaturesCard
 * @property {string} title - Título da funcionalidade exibido em destaque
 * @property {string} description - Descrição breve da funcionalidade
 */
interface Props {
  title: string;
  description: string;
}

defineProps<Props>();
</script>

<template>
  <div
    class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl text-left transition-all duration-300 select-none hover:p-5 hover:bg-blue-50 hover:shadow-sm"
  >
    <!-- Ícone -->
    <div class="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center shrink-0">
      <slot></slot>
    </div>

    <!-- Texto -->
    <div>
      <h3 class="font-semibold text-brand-action text-sm">{{ title }}</h3>
      <p class="text-gray-500 text-xs">{{ description }}</p>
    </div>
  </div>
</template>
