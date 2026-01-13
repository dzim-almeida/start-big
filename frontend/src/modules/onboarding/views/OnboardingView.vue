<script setup lang="ts">
/**
 * @view OnboardingView
 * @description Página principal do fluxo de onboarding.
 * Gerencia a transição entre as etapas de configuração inicial da empresa.
 */

import { computed } from 'vue';
import OnboardingLayout from '../components/ui/OnboardingLayout.vue';
import WelcomeStep from '../components/steps/WelcomeStep.vue';
import SegmentStep from '../components/steps/SegmentStep.vue';
import CompanyStep from '../components/steps/CompanyStep.vue';
import AddressStep from '../components/steps/AddressStep.vue';
import ConfirmationStep from '../components/steps/ConfirmationStep.vue';
import { useOnboarding } from '../composables/useOnboarding';

const { currentStep } = useOnboarding();

/**
 * Componente da etapa atual
 */
const currentStepComponent = computed(() => {
  const steps = {
    0: WelcomeStep,
    1: SegmentStep,
    2: CompanyStep,
    3: AddressStep,
    4: ConfirmationStep,
  };
  return steps[currentStep.value];
});
</script>

<template>
  <OnboardingLayout>
    <Transition
      mode="out-in"
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 translate-x-4"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 -translate-x-4"
    >
      <component :is="currentStepComponent" :key="currentStep" />
    </Transition>
  </OnboardingLayout>
</template>
