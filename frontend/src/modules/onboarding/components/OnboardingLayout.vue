<script setup lang="ts">
/**
 * @component OnboardingLayout
 * @description Layout principal do fluxo de onboarding com background decorativo
 * e área de conteúdo responsiva.
 */

import backgroundImage from '@/assets/images/login/background.png';
import logoImage from '@/assets/images/login/start-logo.png';
import { useOnboarding } from '../composables/useOnboarding';

const { currentStep, progress } = useOnboarding();
</script>

<template>
  <div class="h-screen flex overflow-hidden bg-gray-50">
    <!-- Lado esquerdo - Background decorativo -->
    <div class="hidden lg:flex lg:w-1/2 relative overflow-hidden">
      <img
        :src="backgroundImage"
        alt="Background decorativo"
        class="absolute inset-0 w-full h-full object-cover"
      />
      <!-- Overlay com gradiente sutil -->
      <div class="absolute inset-0 bg-linear-to-br from-brand-primary/10 to-transparent"></div>
    </div>

    <!-- Lado direito - Conteúdo do onboarding -->
    <div
      class="w-full lg:w-1/2 flex flex-col bg-white shadow-2xl overflow-y-scroll"
    >
      <!-- Header com logo e progresso -->
      <header class="sticky top-0 bg-white z-10 px-6 lg:px-12 pt-6 pb-4">
        <div class="flex items-center justify-between mb-4">
          <img :src="logoImage" alt="Start Big Logo" class="h-14 w-auto" />

          <!-- Indicador de progresso (aparece apenas após Step 0) -->
          <div
            v-if="currentStep > 0"
            class="text-sm text-gray-500 font-medium"
          >
            {{ currentStep }} de 4
          </div>
        </div>

        <!-- Barra de progresso -->
        <div
          v-if="currentStep > 0"
          class="h-1.5 bg-gray-100 rounded-full overflow-hidden"
        >
          <div
            class="h-full bg-linear-to-r from-brand-primary to-brand-secondary rounded-full transition-all duration-500 ease-out"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </header>

      <!-- Conteúdo principal -->
      <main class="flex-1 px-6 lg:px-12 py-6">
        <slot />
      </main>

      <!-- Footer -->
      <footer class="px-6 lg:px-12 py-4 border-t border-gray-100">
        <div class="text-center text-[10px] text-gray-400 space-y-0.5">
          <p>
            Copyright &copy; {{ new Date().getFullYear() }} Start Big, LLC. Start Big&trade; is a
            trademark of BigTec, LLC.
          </p>
          <div class="flex justify-center gap-3">
            <a href="#" class="hover:underline">Termos de Serviço</a>
            <span>|</span>
            <a href="#" class="hover:underline">Política de Privacidade</a>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>
