<script setup lang="ts">
/**
 * @component ConfirmationStep
 * @description Tela de confirmação dos dados (Step 4).
 */
import { computed } from 'vue';

// Ícones
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { AlertCircle, Lightbulb, ArrowLeft, CheckCircle2 } from 'lucide-vue-next';

// Componentes Base
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';

// Composables e Constantes
import { useOnboarding } from '../../composables/useOnboarding';
import { getSegmentById } from '../../constants/segments';
import { useConfirmRegisterEmpresa } from '../../composables/useEmpresaForm';

const { confirmSubmit, isPending, apiError } = useConfirmRegisterEmpresa();
const { onboardingData, previousStep } = useOnboarding();

const selectedSegment = computed(() => {
  if (!onboardingData.company.segmento) return null;
  return getSegmentById(onboardingData.company.segmento);
});

const companyFields = computed(() => [
  { label: 'Razão social', value: onboardingData.company.razaoSocial },
  { label: 'Nome Fantasia', value: onboardingData.company.nomeFantasia },
  { label: onboardingData.company.tipoDocumento, value: onboardingData.company.documento },
  { label: 'Celular', value: onboardingData.contact.celular },
  { label: 'Email', value: onboardingData.contact.email },
  { label: 'Telefone', value: onboardingData.contact.telefone, hideIfEmpty: true },
]);

const addressFields = computed(() => [
  { label: 'CEP', value: onboardingData.address.cep },
  { label: 'Logradouro/Rua', value: onboardingData.address.logradouro },
  { label: 'Número', value: onboardingData.address.numero || 'S/N' },
  { label: 'Bairro', value: onboardingData.address.bairro },
  { label: 'Complemento', value: onboardingData.address.complemento, hideIfEmpty: true },
  { label: 'Cidade', value: onboardingData.address.cidade },
  { label: 'Estado', value: onboardingData.address.estado },
]);
</script>

<template>
  <div>
    <div
      v-if="apiError"
      class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3"
    >
      <div
        class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center shrink-0 text-red-600"
      >
        <LucideIcon :icon="AlertCircle" />
      </div>
      <p class="text-sm text-red-700">{{ apiError }}</p>
    </div>

    <div class="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
      <div class="p-6 border-b border-gray-100">
        <p class="text-xs text-gray-500 mb-2">Seguimento</p>
        <div class="flex items-center gap-3">
          <div class="p-2 bg-blue-50 rounded-xl">
            <SegmentIcons v-if="selectedSegment" :icon="selectedSegment.icon" size="md" />
          </div>
          <span class="font-semibold text-brand-action">{{ selectedSegment?.label }}</span>
        </div>
      </div>

      <div class="p-6 border-b border-gray-100">
        <div class="grid grid-cols-2 gap-6">
          <template v-for="field in companyFields" :key="field.label">
            <div v-if="!field.hideIfEmpty || field.value">
              <p class="text-xs text-gray-500 mb-1">{{ field.label }}</p>
              <p class="font-medium text-brand-action text-sm">{{ field.value }}</p>
            </div>
          </template>
        </div>
      </div>

      <div class="p-6">
        <div class="grid grid-cols-2 gap-6">
          <template v-for="field in addressFields" :key="field.label">
            <div v-if="!field.hideIfEmpty || field.value">
              <p class="text-xs text-gray-500 mb-1">{{ field.label }}</p>
              <p class="font-medium text-brand-action text-sm">{{ field.value }}</p>
            </div>
          </template>
        </div>
      </div>
    </div>

    <div class="mt-6 p-4 bg-amber-50 border border-amber-100 rounded-xl flex items-start gap-3">
      <div
        class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center shrink-0 text-amber-600"
      >
        <LucideIcon :icon="Lightbulb" />
      </div>
      <p class="text-sm text-amber-800">
        O sistema será personalizado para
        <strong class="underline">{{ selectedSegment?.label }}</strong
        >.
      </p>
    </div>

    <div class="flex gap-4 mt-8">
      <BaseButton
        type="button"
        variant="secondary"
        size="lg"
        class="flex-1"
        :disabled="isPending"
        @click="previousStep"
      >
        <LucideIcon :icon="ArrowLeft" />
        Voltar
      </BaseButton>
      <BaseButton size="lg" class="flex-1" :is-loading="isPending" @click="confirmSubmit">
        <LucideIcon :icon="CheckCircle2" />
        Salvar
      </BaseButton>
    </div>
  </div>
</template>
