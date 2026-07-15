<script setup lang="ts">
/**
 * @component EscolhaActionStep
 * @description Tela inicial para escolher entre Autocadastro e Reconexão.
 */

import { computed } from 'vue';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowRight, LogIn, UserPlus } from 'lucide-vue-next';

import { useSignIn } from '../../composables/useSignIn';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import RocketAnimation from '@/shared/components/animations/RocketAnimation.vue';

const { signInMode } = useSignIn();

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Bom dia';
  if (hour < 18) return 'Boa tarde';
  return 'Boa noite';
});

function startAutocadastro() {
  signInMode.value = 'autocadastro';
}

function startReconnect() {
  signInMode.value = 'reconnect';
}
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
        Bem-vindo ao<br />
        <span class="text-brand-primary">Start Big ERP</span>
      </h1>

      <p class="text-gray-500 text-base max-w-md mx-auto leading-relaxed">
        Como você deseja começar?
      </p>
    </div>

    <div class="flex flex-col gap-4 max-w-xs mx-auto">
      <BaseButton size="lg" variant="primary" class="w-full flex justify-between" @click="startAutocadastro">
        <span class="flex items-center gap-2">
          <LucideIcon :icon="UserPlus" />
          Fazer Autocadastro
        </span>
        <LucideIcon :icon="ArrowRight" />
      </BaseButton>
      
      <BaseButton size="lg" variant="ghost" class="w-full flex justify-between" @click="startReconnect">
        <span class="flex items-center gap-2">
          <LucideIcon :icon="LogIn" />
          Já tenho uma licença
        </span>
        <LucideIcon :icon="ArrowRight" />
      </BaseButton>
    </div>

  </div>
</template>
