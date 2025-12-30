<script setup lang="ts">
/**
 * @component WelcomeStep
 * @description Tela de boas-vindas do onboarding (Step 0).
 * Apresenta uma saudação calorosa e introduz o processo de configuração.
 */

import { computed } from 'vue';
import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import { useOnboarding } from '../../composables/useOnboarding';

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
      <div class="w-32 h-32 mx-auto relative">
        <!-- Círculo de fundo animado -->
        <div class="absolute inset-0 bg-linear-to-br from-brand-primary/20 to-brand-secondary/20 rounded-full animate-pulse"></div>

        <!-- Ícone de foguete -->
        <svg
          class="w-full h-full p-6 text-brand-primary relative"
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <!-- Foguete -->
          <path
            d="M32 4C32 4 16 16 16 36C16 44 20 52 32 56C44 52 48 44 48 36C48 16 32 4 32 4Z"
            fill="currentColor"
            opacity="0.2"
          />
          <path
            d="M32 8C32 8 20 18 20 34C20 40 23 46 32 50C41 46 44 40 44 34C44 18 32 8 32 8Z"
            fill="currentColor"
          />
          <!-- Janela -->
          <circle cx="32" cy="26" r="6" fill="white" opacity="0.9"/>
          <circle cx="32" cy="26" r="4" fill="#E3F2FD"/>
          <!-- Chamas -->
          <path d="M28 52L32 60L36 52" fill="#FF9800"/>
          <path d="M30 52L32 58L34 52" fill="#FFCA28"/>
          <!-- Asas -->
          <path d="M16 40L20 36V44L16 40Z" fill="currentColor" opacity="0.7"/>
          <path d="M48 40L44 36V44L48 40Z" fill="currentColor" opacity="0.7"/>
        </svg>

        <!-- Partículas decorativas -->
        <div class="absolute -top-2 -right-2 w-3 h-3 bg-brand-secondary rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
        <div class="absolute top-4 -left-4 w-2 h-2 bg-brand-primary rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
        <div class="absolute -bottom-1 right-4 w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.5s"></div>
      </div>
    </div>

    <!-- Saudação -->
    <div class="space-y-4 mb-10">
      <p class="text-brand-secondary font-medium text-lg">{{ greeting }}!</p>

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
      <div
        v-for="(feature, index) in features"
        :key="feature.title"
        class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl text-left transition-all duration-300 hover:bg-blue-50 hover:shadow-sm"
        :style="{ animationDelay: `${index * 0.1}s` }"
      >
        <!-- Ícone -->
        <div class="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center shrink-0">
          <!-- Chart icon -->
          <svg v-if="feature.icon === 'chart'" class="w-6 h-6 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <!-- Clock icon -->
          <svg v-else-if="feature.icon === 'clock'" class="w-6 h-6 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Shield icon -->
          <svg v-else-if="feature.icon === 'shield'" class="w-6 h-6 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>

        <!-- Texto -->
        <div>
          <h3 class="font-semibold text-brand-action text-sm">{{ feature.title }}</h3>
          <p class="text-gray-500 text-xs">{{ feature.description }}</p>
        </div>
      </div>
    </div>

    <!-- Botão de ação -->
    <BaseButton
      size="lg"
      class="w-full max-w-xs mx-auto"
      @click="nextStep"
    >
      Começar Configuração
      <svg class="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
      </svg>
    </BaseButton>

    <!-- Tempo estimado -->
    <p class="mt-4 text-xs text-gray-400">
      Tempo estimado: 3-5 minutos
    </p>
  </div>
</template>
