<script setup lang="ts">
/**
 * @component ObservacoesSection
 * @description Form section for employee observations/notes
 */

import { FileText } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';

import { useEmployeeForm } from '../../composables/useEmployeeForm';

// =============================================
// Props
// =============================================

interface Props {
  submitCount: number;
  disabled?: boolean;
}

const props = defineProps<Props>();

// =============================================
// Form Fields
// =============================================

const { observacao, errors } = useEmployeeForm();
</script>

<template>
  <section>
    <!-- Section Header -->
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-zinc-100 rounded-xl flex items-center justify-center text-zinc-600"
      >
        <LucideIcon :icon="FileText" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Observacoes</h3>
    </div>

    <div>
      <label class="block text-xs font-medium text-gray-700 mb-1">
        Observacoes Internas
      </label>
      <textarea
        v-model="observacao"
        class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary transition-colors resize-none"
        :class="{
          'border-red-500 focus:border-red-500 focus:ring-red-500/20':
            submitCount > 0 && errors.observacao,
          'bg-gray-50 cursor-not-allowed': disabled,
        }"
        rows="4"
        placeholder="Anotacoes internas sobre o funcionario (opcional)..."
        maxlength="500"
        :disabled="disabled"
      />
      <div class="flex justify-between mt-1">
        <p
          v-if="submitCount > 0 && errors.observacao"
          class="text-xs text-red-500"
        >
          {{ errors.observacao }}
        </p>
        <span class="text-xs text-zinc-400 ml-auto">
          {{ observacao?.length || 0 }}/500
        </span>
      </div>
    </div>
  </section>
</template>
