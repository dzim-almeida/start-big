<script setup lang="ts">
/**
 * @component ContactSection
 * @description Seção de dados de contato (email, telefone, celular)
 * Refatorado para usar inject pattern
 */

import { Phone } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { SECTION_LABELS } from '../../constants/empresa.constants';
import { useEmpresaForm } from '../../composables/useEmpresaFormProvider';

// =============================================
// Props (apenas para compatibilidade durante transição)
// =============================================

interface Props {
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

// =============================================
// Inject Context
// =============================================

const {
  email,
  telefone,
  celular,
  errors,
  submitCount,
} = useEmpresaForm();
</script>

<template>
  <section class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600"
      >
        <LucideIcon :icon="Phone"/>
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">{{ SECTION_LABELS.contato }}</h3>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Email Corporativo -->
      <div class="md:col-span-2">
        <BaseInput
          v-model="email"
          label="E-mail Corporativo"
          type="email"
          placeholder="contato@suaempresa.com.br"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.email : ''"
        />
      </div>

      <!-- Telefone Fixo -->
      <BaseInput
        v-model="telefone"
        label="Telefone Fixo"
        type="tel"
        mask="(##) ####-####"
        placeholder="(00) 0000-0000"
        :disabled="disabled"
        :error="submitCount > 0 ? errors.telefone : ''"
      />

      <!-- Celular / WhatsApp -->
      <BaseInput
        v-model="celular"
        label="Celular / WhatsApp"
        type="tel"
        mask="(##) #####-####"
        placeholder="(00) 90000-0000"
        :disabled="disabled"
        :error="submitCount > 0 ? errors.celular : ''"
      />
    </div>
  </section>
</template>
