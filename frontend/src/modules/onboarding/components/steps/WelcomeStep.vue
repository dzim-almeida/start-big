<script setup lang="ts">
/**
 * @component WelcomeStep
 * @description Tela de boas-vindas do onboarding (Step 0).
 * Apresenta uma saudação calorosa e introduz o processo de configuração.
 */

import { computed } from 'vue';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowRight } from 'lucide-vue-next';

import { useOnboarding } from '../../composables/useOnboarding';
import { FEATURES_OPTIONS } from '../../constants/features';

import FeaturesCard from '../ui/FeaturesCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import RocketAnimation from '@/shared/components/animations/RocketAnimation.vue';

const { nextStep } = useOnboarding();

/**
 * Retorna uma saudação baseada na hora do dia
 */
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Bom dia';
  if (hour < 18) return 'Boa tarde';
  return 'Boa noite';
});
</script>

<template>
  <div class="max-w-lg mx-auto text-center py-8">
    <!-- Ilustração animada -->
    <div class="mb-8 relative">
      <RocketAnimation />
    </div>

    <!-- Saudação -->
    <div class="space-y-4 mb-10">
      <p class="text-brand-secondary font-bold text-lg -mb-0.5">{{ greeting }}!</p>

      <h1 class="text-3xl lg:text-4xl font-bold text-brand-action leading-tight">
        Vamos configurar<br />
        <span class="text-brand-primary">sua empresa</span>
      </h1>

      <p class="text-gray-500 text-base max-w-md mx-auto leading-relaxed">
        Em apenas <strong class="text-brand-action">4 passos simples</strong>, você terá acesso
        completo ao sistema Start Big, personalizado para o seu negócio.
      </p>
    </div>

    <!-- Cards de features -->
    <div class="grid gap-4 mb-10">
      <FeaturesCard
        v-for="(feat, index) in FEATURES_OPTIONS"
        :key="index"
        :title="feat.title"
        :description="feat.description"
      >
        <component class="text-brand-primary" :is="feat.icon" :size="24"></component>
      </FeaturesCard>
    </div>

    <!-- Botão de ação -->
    <BaseButton size="lg" class="w-full max-w-xs mx-auto" @click="nextStep">
      Começar Configuração
      <LucideIcon :icon="ArrowRight" />
    </BaseButton>

    <!-- Tempo estimado -->
    <p class="mt-4 text-xs text-gray-400">Tempo estimado: 3-5 minutos</p>
  </div>
</template>
