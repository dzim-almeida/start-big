<script setup lang="ts">
/**
 * @component SegmentoStep
 * @description Seleção do segmento de negócio (Passo 1).
 */
import { computed } from 'vue';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useSignIn } from '../../composables/useSignIn';
import { BUSINESS_SEGMENTS, getSegmentById } from '../../constants/segments';
import SegmentCard from '../ui/SegmentCard.vue';

import type { BusinessSegment } from '../../types/sign-in.types';

const { signInData, updateLojaData, nextStep, previousStep } = useSignIn();

const selectedSegment = computed(() => signInData.loja.segmento);

const selectedSegmentLabel = computed(() => {
  if (!selectedSegment.value) return '';
  return getSegmentById(selectedSegment.value)?.label || '';
});

function selectSegment(id: BusinessSegment): void {
  updateLojaData({ segmento: id });
}

function handleNext(): void {
  if (selectedSegment.value) {
    nextStep();
  }
}
</script>

<template>
  <div>
    <div class="text-center mb-6">
      <h2 class="text-xl font-bold text-brand-action mb-2">
        Qual é o segmento do seu negócio?
      </h2>
      <p class="text-gray-500 text-sm">
        Selecione o tipo de atividade principal da sua empresa
      </p>
    </div>

    <!-- Grid de segmentos -->
    <div class="grid grid-cols-2 gap-3 mb-6">
      <SegmentCard
        v-for="segment in BUSINESS_SEGMENTS"
        :key="segment.id"
        :segment="segment"
        :selected="selectedSegment === segment.id"
        @select="selectSegment(segment.id)"
      />
    </div>

    <!-- Confirmação do segmento selecionado -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-if="selectedSegment"
        class="p-3 mb-6 bg-green-50 border border-green-100 rounded-lg flex items-center gap-2"
      >
        <LucideIcon :icon="CheckCircle2" size="md" class="text-green-600 shrink-0" />
        <p class="text-xs text-green-700">
          O sistema será personalizado para
          <strong>{{ selectedSegmentLabel }}</strong>
          com campos e recursos específicos.
        </p>
      </div>
    </Transition>

    <!-- Botões -->
    <div class="flex gap-4">
      <BaseButton
        type="button"
        variant="secondary"
        size="lg"
        class="flex-1"
        @click="previousStep"
      >
        <LucideIcon :icon="ArrowLeft" />
        Voltar
      </BaseButton>
      <BaseButton
        size="lg"
        class="flex-1"
        :disabled="!selectedSegment"
        @click="handleNext"
      >
        Próximo
        <LucideIcon :icon="ArrowRight" />
      </BaseButton>
    </div>
  </div>
</template>
