<script setup lang="ts">
/**
 * @component SegmentStep
 * @description Tela de seleção de segmento de negócio (Step 1).
 * Apresenta os segmentos disponíveis em um grid responsivo.
 */

import { computed } from 'vue';
import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import SegmentCard from '../SegmentCard.vue';
import { useOnboarding } from '../../composables/useOnboarding';
import { BUSINESS_SEGMENTS } from '../../constants/segments';
import type { BusinessSegment } from '../../types/onboarding.types';

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

/**
 * Handler para avançar
 */
function handleNext() {
  if (canProceed.value) {
    nextStep();
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Header da etapa -->
    <div class="text-center mb-8">
      <p class="text-brand-primary font-medium text-sm mb-2">
        Etapa 1 de 4 - Qual o seguimento da sua empresa?
      </p>
      <h1 class="text-2xl lg:text-3xl font-bold text-brand-action mb-3">
        Configuração Inicial
      </h1>
      <p class="text-gray-500 text-sm max-w-md mx-auto">
        Configure sua empresa para começar a usar o sistema
      </p>
    </div>

    <!-- Subtítulo -->
    <div class="mb-6">
      <p class="text-gray-600 text-sm">
        Selecione o seguimento para personalizarmos o sistema de acordo com suas necessidades.
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
      <div class="w-8 h-8 bg-brand-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
        <svg class="w-4 h-4 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p class="text-sm text-gray-600">
        O sistema será personalizado para
        <strong class="text-brand-primary">
          {{ BUSINESS_SEGMENTS.find(s => s.id === onboardingData.company.segmento)?.label }}
        </strong>
        com campos e recursos específicos para seu segmento.
      </p>
    </div>

    <!-- Botões de navegação -->
    <div class="flex gap-4">
      <BaseButton
        variant="secondary"
        size="lg"
        class="flex-1"
        @click="previousStep"
      >
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
        </svg>
        Voltar
      </BaseButton>

      <BaseButton
        size="lg"
        class="flex-1"
        :disabled="!canProceed"
        @click="handleNext"
      >
        Salvar
        <svg class="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </BaseButton>
    </div>
  </div>
</template>
