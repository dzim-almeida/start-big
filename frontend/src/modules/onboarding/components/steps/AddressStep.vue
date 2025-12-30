<script setup lang="ts">
/**
 * @component AddressStep
 * @description Tela de endereço da empresa (Step 3).
 * Formulário com busca automática de CEP via ViaCEP.
 */

import { watch } from 'vue';
import { useForm } from 'vee-validate';
import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/BaseInput/BaseInput.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';
import { useOnboarding } from '../../composables/useOnboarding';
import { useCepLookup } from '../../composables/useCepLookup';
import { addressValidationSchema, type AddressFormData } from '../../schemas/onboarding.schema';

const { onboardingData, updateAddressData, nextStep, previousStep } = useOnboarding();
const { isLoading: isCepLoading, error: cepError, lookupCep } = useCepLookup();

/**
 * Configuração do formulário
 */
const { handleSubmit, errors, defineField, submitCount, setValues } = useForm<AddressFormData>({
  validationSchema: addressValidationSchema,
  initialValues: {
    cep: onboardingData.address.cep,
    logradouro: onboardingData.address.logradouro,
    numero: onboardingData.address.numero,
    complemento: onboardingData.address.complemento,
    bairro: onboardingData.address.bairro,
    cidade: onboardingData.address.cidade,
    estado: onboardingData.address.estado,
  },
});

/**
 * Definição dos campos
 */
const [cep] = defineField('cep');
const [logradouro] = defineField('logradouro');
const [numero] = defineField('numero');
const [complemento] = defineField('complemento');
const [bairro] = defineField('bairro');
const [cidade] = defineField('cidade');
const [estado] = defineField('estado');

/**
 * Watch para busca automática de CEP
 */
watch(cep, async (newCep) => {
  if (!newCep) return;

  const cleanCep = newCep.replace(/\D/g, '');
  if (cleanCep.length === 8) {
    const data = await lookupCep(newCep);
    if (data) {
      setValues({
        cep: newCep,
        logradouro: data.logradouro || '',
        bairro: data.bairro || '',
        cidade: data.localidade || '',
        estado: data.uf || '',
        numero: '',
        complemento: data.complemento || '',
      });
    }
  }
});

/**
 * Handler de submit
 */
const onSubmit = handleSubmit((formData) => {
  updateAddressData({
    cep: formData.cep,
    logradouro: formData.logradouro,
    numero: formData.numero,
    complemento: formData.complemento || '',
    bairro: formData.bairro,
    cidade: formData.cidade,
    estado: formData.estado,
  });

  nextStep();
});
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Header da etapa -->
    <div class="text-center mb-8">
      <p class="text-brand-primary font-medium text-sm mb-2">
        Etapa 3 de 4 - Endereço
      </p>
      <h1 class="text-2xl lg:text-3xl font-bold text-brand-action mb-3">
        Configuração Inicial
      </h1>
      <p class="text-gray-500 text-sm max-w-md mx-auto">
        Configure sua empresa para começar a usar o sistema
      </p>
    </div>

    <form @submit.prevent="onSubmit" class="space-y-6">
      <!-- Seção: Endereço -->
      <section>
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <SegmentIcons icon="building" size="sm" />
          </div>
          <h2 class="text-lg font-semibold text-brand-action">Endereço</h2>
        </div>

        <div class="grid grid-cols-12 gap-4">
          <!-- CEP -->
          <div class="col-span-12 md:col-span-3">
            <div class="relative">
              <BaseInput
                v-model="cep"
                label="CEP"
                placeholder="XXXXX-XXX"
                mask="#####-###"
                :error="submitCount > 0 ? errors.cep : ''"
                :disabled="isCepLoading"
              />
              <!-- Loading indicator -->
              <div
                v-if="isCepLoading"
                class="absolute right-3 top-8"
              >
                <svg class="animate-spin h-4 w-4 text-brand-primary" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </div>
            <!-- Erro do CEP -->
            <p v-if="cepError" class="mt-1 text-xs text-amber-600">
              {{ cepError }}
            </p>
          </div>

          <!-- Logradouro -->
          <div class="col-span-12 md:col-span-7">
            <BaseInput
              v-model="logradouro"
              label="Logradouro/Rua"
              placeholder="Digite o logradouro"
              :error="submitCount > 0 ? errors.logradouro : ''"
            />
          </div>

          <!-- Número -->
          <div class="col-span-12 md:col-span-2">
            <BaseInput
              v-model="numero"
              label="Número"
              placeholder="Nº"
              :error="submitCount > 0 ? errors.numero : ''"
            />
          </div>

          <!-- Complemento -->
          <div class="col-span-12 md:col-span-6">
            <BaseInput
              v-model="complemento"
              label="Complemento"
              placeholder="Apto, Sala, etc. (opcional)"
              :error="submitCount > 0 ? errors.complemento : ''"
            />
          </div>

          <!-- Bairro -->
          <div class="col-span-12 md:col-span-6">
            <BaseInput
              v-model="bairro"
              label="Bairro"
              placeholder="Digite o bairro"
              :error="submitCount > 0 ? errors.bairro : ''"
            />
          </div>

          <!-- Cidade -->
          <div class="col-span-12 md:col-span-8">
            <BaseInput
              v-model="cidade"
              label="Cidade"
              placeholder="Digite a cidade"
              :error="submitCount > 0 ? errors.cidade : ''"
            />
          </div>

          <!-- Estado -->
          <div class="col-span-12 md:col-span-4">
            <BaseInput
              v-model="estado"
              label="Estado"
              placeholder="UF"
              :error="submitCount > 0 ? errors.estado : ''"
            />
          </div>
        </div>
      </section>

      <!-- Dica -->
      <div class="p-4 bg-amber-50 border border-amber-100 rounded-xl flex items-start gap-3">
        <div class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center shrink-0">
          <svg class="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <p class="text-sm text-amber-800">
          <strong>Dica:</strong> Digite o CEP e os campos serão preenchidos automaticamente!
        </p>
      </div>

      <!-- Botões de navegação -->
      <div class="flex gap-4 pt-4">
        <BaseButton
          type="button"
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
          type="submit"
          size="lg"
          class="flex-1"
        >
          Salvar
          <svg class="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </BaseButton>
      </div>
    </form>
  </div>
</template>
