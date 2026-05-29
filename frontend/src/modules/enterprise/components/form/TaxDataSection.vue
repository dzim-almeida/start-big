<script setup lang="ts">
/**
 * @component TaxDataSection
 * @description Seção de dados fiscais (IE, IM, Regime Tributário)
 * Refatorado para usar inject pattern
 */

import { Landmark } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { SECTION_LABELS, REGIME_TRIBUTARIO_OPTIONS } from '../../constants/empresa.constants';
import { useEmpresaForm } from '../../composables/useEmpresaFormProvider';

// =============================================
// Props
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
  inscricao_estadual,
  inscricao_municipal,
  regime_tributario,
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
        <LucideIcon :icon="Landmark"/>
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">{{ SECTION_LABELS.dadosFiscais }}</h3>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Inscrição Estadual -->
      <BaseInput
        v-model="inscricao_estadual"
        label="Inscrição Estadual (IE)"
        type="text"
        placeholder="Ex: Isento"
        :disabled="disabled"
        :error="submitCount > 0 ? errors.inscricao_estadual : ''"
      />

      <!-- Inscrição Municipal -->
      <BaseInput
        v-model="inscricao_municipal"
        label="Inscrição Municipal (IM)"
        type="text"
        :disabled="disabled"
        :error="submitCount > 0 ? errors.inscricao_municipal : ''"
      />

      <!-- Regime Tributário -->
      <div class="md:col-span-2">
        <BaseSelect
          v-model="regime_tributario"
          label="Regime Tributário"
          :options="REGIME_TRIBUTARIO_OPTIONS"
          placeholder="Selecione o regime..."
          :disabled="disabled"
          :error="submitCount > 0 ? errors.regime_tributario : ''"
        />
      </div>
    </div>
  </section>
</template>
