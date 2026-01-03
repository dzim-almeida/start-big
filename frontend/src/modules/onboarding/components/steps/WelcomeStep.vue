<script setup lang="ts">
/**
 * @component WelcomeStep
 * @description Tela de boas-vindas do onboarding (Step 0).
 * Apresenta uma saudação calorosa e introduz o processo de configuração.
 */

import { computed } from 'vue';
import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import { useOnboarding } from '../../composables/useOnboarding';
import RocketAnimation from '../animations/RocketAnimation.vue';
import FeaturesCard from '../FeaturesCard.vue';
import Icons from '../icons/Icons.vue';
import DirectionsIcons from '../icons/Icons.vue';

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

/**
 * Features do sistema para exibir
 */
const features = [
  {
    icon: 'chart',
    title: 'Gestão Inteligente',
    description: 'Controle completo do seu negócio em um só lugar',
  },
  {
    icon: 'clock',
    title: 'Economia de Tempo',
    description: 'Automatize processos e foque no que importa',
  },
  {
    icon: 'shield',
    title: 'Segurança Total',
    description: 'Seus dados protegidos com tecnologia de ponta',
  },
];
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
        Vamos configurar<br/>
        <span class="text-brand-primary">sua empresa</span>
      </h1>

      <p class="text-gray-500 text-base max-w-md mx-auto leading-relaxed">
        Em apenas <strong class="text-brand-action">4 passos simples</strong>, você terá acesso completo
        ao sistema Start Big, personalizado para o seu negócio.
      </p>
    </div>

    <!-- Cards de features -->
    <div class="grid gap-4 mb-10">
      <FeaturesCard 
        v-for="(feat, index) in features"
        :key="index"
        :title="feat.title"
        :description="feat.description"
      >
        <Icons :icon="feat.icon" />
      </FeaturesCard>
    </div>

    <!-- Botão de ação -->
    <BaseButton
      size="lg"
      class="w-full max-w-xs mx-auto"
      @click="nextStep"
    >
      Começar Configuração
      <DirectionsIcons icon="next" />
    </BaseButton>

    <!-- Tempo estimado -->
    <p class="mt-4 text-xs text-gray-400">
      Tempo estimado: 3-5 minutos
    </p>
  </div>
</template>
