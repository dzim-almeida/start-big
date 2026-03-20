<script setup lang="ts">
/**
 * @component NotesSection
 * @description Form section for customer notes/observations
 */

import { FileText } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { useCustomerForm } from '@/modules/customers/composables/modal/context/useCustomerForm.context';

// =============================================
// Props
// =============================================

interface Props {
  disabled?: boolean;
}

defineProps<Props>();

// =============================================
// Form Fields
// =============================================

const { observacoes } = useCustomerForm();
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
      <h3 class="text-lg font-semibold text-zinc-800">Observações</h3>
    </div>

    <textarea
      v-model="observacoes"
      class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
      rows="3"
      placeholder="Observações adicionais sobre o cliente (opcional)"
      :disabled="disabled"
    ></textarea>
  </section>
</template>
