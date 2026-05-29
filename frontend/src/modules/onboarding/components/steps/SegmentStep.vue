<script setup lang="ts">
/**
 * @component SegmentStep
 * @description Tela de seleção de segmento de negócio (Step 1).
 * Apresenta os segmentos disponíveis em um grid responsivo.
 */

import { computed } from 'vue';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowRight, ArrowLeft, Info } from 'lucide-vue-next';

import { useOnboarding } from '../../composables/useOnboarding';
import { BUSINESS_SEGMENTS } from '../../constants/segments';
import type { BusinessSegment } from '../../types/onboarding.types';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import SegmentCard from '../ui/SegmentCard.vue';

const { onboardingData, setSegment, nextStep, previousStep } = useOnboarding();

/**
 * Computed para verificar se pode avançar
 */
const canProceed = computed(() => onboardingData.company.segmento !== null);

/**
 * Handler para seleção de segmento
 */
function handleSegmentSelect(id: BusinessSegment) {
  setSegment(id);
}
</script>

<template>
  <div>
    <!-- Subtítulo -->
    <div class="mb-6">
      <p class="text-gray-600 text-sm">
        Selecione o segmento para personalizarmos o sistema de acordo com suas necessidades.
      </p>
    </div>

    <!-- Grid de segmentos -->
    <div class="grid grid-cols-2 gap-4 mb-8">
      <SegmentCard
        v-for="segment in BUSINESS_SEGMENTS"
        :key="segment.id"
        :id="segment.id"
        :label="segment.label"
        :icon="segment.icon"
        :selected="onboardingData.company.segmento === segment.id"
        @select="handleSegmentSelect"
      />
    </div>

    <!-- Mensagem de seleção -->
    <div
      v-if="onboardingData.company.segmento"
      class="mb-6 p-4 bg-blue-50 border border-blue-100 rounded-xl flex items-start gap-3"
    >
      <div
        class="w-8 h-8 bg-brand-primary/10 rounded-full flex items-center justify-center shrink-0"
      >
        <LucideIcon :icon="Info" />
      </div>
      <p class="text-sm text-gray-600">
        O sistema será personalizado para
        <strong class="text-brand-primary">
          {{ BUSINESS_SEGMENTS.find((s) => s.id === onboardingData.company.segmento)?.label }}
        </strong>
        com campos e recursos específicos para seu segmento.
      </p>
    </div>

    <!-- Botões de navegação -->
    <div class="flex gap-4">
      <BaseButton variant="secondary" size="lg" class="flex-1" @click="previousStep">
        <LucideIcon :icon="ArrowLeft" />
        Voltar
      </BaseButton>

      <BaseButton size="lg" class="flex-1" :disabled="!canProceed" @click="nextStep">
        Salvar
        <LucideIcon :icon="ArrowRight" />
      </BaseButton>
    </div>
  </div>
</template>
