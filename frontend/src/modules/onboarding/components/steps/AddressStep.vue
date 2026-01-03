<script setup lang="ts">
/**
 * @component AddressStep
 * @description Tela de endereço da empresa (Step 3).
 * Formulário com busca automática de CEP via ViaCEP.
 */

import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/BaseSelect/BaseSelect.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';
import { useOnboarding } from '../../composables/useOnboarding';
import { useAddressForm } from '../../composables/useEmpresaForm';
import Icons from '../icons/Icons.vue';
import { ESTADOS_BRASILEIROS } from '@/shared/constants/estados.constant';

const { previousStep } = useOnboarding();

const {
  cep,
  logradouro,
  numero,
  complemento,
  bairro,
  cidade,
  estado,
  errors,
  cepIsLoading,
  cepIsError,
  onSubmit,
  submitCount,
} = useAddressForm();
</script>

<template>
  <div>
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
                :required="true"
                mask="#####-###"
                :error="submitCount > 0 ? errors.cep : ''"
                :disabled="cepIsLoading"
              />
              <!-- Loading indicator -->
              <div
                v-if="cepIsLoading"
                class="absolute right-3 top-8"
              >
                <svg class="animate-spin h-4 w-4 text-brand-primary" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </div>
            <!-- Erro do CEP -->
            <p v-if="cepIsError" class="mt-1 text-xs text-amber-600">
              CEP não encontrado
            </p>
          </div>

          <!-- Logradouro -->
          <div class="col-span-12 md:col-span-7">
            <BaseInput
              v-model="logradouro"
              label="Logradouro/Rua"
              placeholder="Digite o logradouro"
              :required="true"
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
              :required="true"
              :error="submitCount > 0 ? errors.bairro : ''"
            />
          </div>

          <!-- Cidade -->
          <div class="col-span-12 md:col-span-8">
            <BaseInput
              v-model="cidade"
              label="Cidade"
              placeholder="Digite a cidade"
              :required="true"
              :error="submitCount > 0 ? errors.cidade : ''"
            />
          </div>

          <!-- Estado -->
          <div class="col-span-12 md:col-span-4">
            <BaseSelect
              v-model="estado"
              label="Estado"
              placeholder="Selecione o estado"
              :options="ESTADOS_BRASILEIROS"
              :required="true"
              :error="submitCount > 0 ? errors.estado : ''"
            />
          </div>
        </div>
      </section>

      <!-- Dica -->
      <div class="p-4 bg-amber-50 border border-amber-100 rounded-xl flex items-start gap-3">
        <div class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center shrink-0">
          <Icons icon="light" />
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
          <Icons icon="back" />
          Voltar
        </BaseButton>

        <BaseButton
          type="submit"
          size="lg"
          class="flex-1"
        >
          Salvar
          <Icons icon="next" />
        </BaseButton>
      </div>
    </form>
  </div>
</template>
