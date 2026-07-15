<script setup lang="ts">
/**
 * @view SignInView
 * @description Página principal do fluxo de sign-in.
 * Gerencia a transição entre as etapas de configuração inicial do sistema.
 */

import { computed } from 'vue';
import SignInLayout from '../components/ui/SignInLayout.vue';
import EscolhaActionStep from '../components/steps/EscolhaActionStep.vue';
import ReconnectStep from '../components/steps/ReconnectStep.vue';
import ApresentacaoStep from '../components/steps/ApresentacaoStep.vue';
import SegmentoStep from '../components/steps/SegmentoStep.vue';
import LojaStep from '../components/steps/LojaStep.vue';
import ResponsavelStep from '../components/steps/ResponsavelStep.vue';
import AcessoStep from '../components/steps/AcessoStep.vue';
import ResumoStep from '../components/steps/ResumoStep.vue';
import { useSignIn } from '../composables/useSignIn';

const { currentStep, signInMode } = useSignIn();

const currentStepComponent = computed(() => {
  if (signInMode.value === 'choice') return EscolhaActionStep;
  if (signInMode.value === 'reconnect') return ReconnectStep;

  const steps = {
    0: ApresentacaoStep,
    1: SegmentoStep,
    2: LojaStep,
    3: ResponsavelStep,
    4: AcessoStep,
    5: ResumoStep,
  };
  return steps[currentStep.value];
});
</script>

<template>
  <SignInLayout>
    <Transition
      mode="out-in"
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 translate-x-4"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 -translate-x-4"
    >
      <component :is="currentStepComponent" :key="signInMode === 'autocadastro' ? currentStep : signInMode" />
    </Transition>
  </SignInLayout>
</template>
