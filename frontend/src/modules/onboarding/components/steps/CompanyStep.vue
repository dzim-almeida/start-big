<script setup lang="ts">
/**
 * @component CompanyStep
 * @description Tela de dados da empresa (Step 2).
 * Formulário com razão social, nome fantasia, documento e contatos.
 */

import { computed } from 'vue';
import { useForm } from 'vee-validate';
import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/BaseInput/BaseInput.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';
import { useOnboarding } from '../../composables/useOnboarding';
import { companyValidationSchema, type CompanyFormData } from '../../schemas/onboarding.schema';
import { getSegmentById } from '../../constants/segments';
import type { DocumentType } from '../../types/onboarding.types';

const {
  onboardingData,
  updateCompanyData,
  updateContactData,
  setDocumentType,
  nextStep,
  previousStep,
} = useOnboarding();

/**
 * Configuração do formulário
 */
const { handleSubmit, errors, defineField, submitCount, setFieldValue } = useForm<CompanyFormData>({
  validationSchema: companyValidationSchema,
  initialValues: {
    razaoSocial: onboardingData.company.razaoSocial,
    nomeFantasia: onboardingData.company.nomeFantasia,
    tipoDocumento: onboardingData.company.tipoDocumento,
    documento: onboardingData.company.documento,
    celular: onboardingData.contact.celular,
    email: onboardingData.contact.email,
    telefone: onboardingData.contact.telefone,
  },
});

/**
 * Definição dos campos
 */
const [razaoSocial] = defineField('razaoSocial');
const [nomeFantasia] = defineField('nomeFantasia');
const [tipoDocumento] = defineField('tipoDocumento');
const [documento] = defineField('documento');
const [celular] = defineField('celular');
const [email] = defineField('email');
const [telefone] = defineField('telefone');

/**
 * Segmento selecionado
 */
const selectedSegment = computed(() => {
  if (!onboardingData.company.segmento) return null;
  return getSegmentById(onboardingData.company.segmento);
});

/**
 * Máscara do documento baseada no tipo
 */
const documentMask = computed(() => {
  return tipoDocumento.value === 'CNPJ' ? '##.###.###/####-##' : '###.###.###-##';
});

/**
 * Handler para mudança de tipo de documento
 */
function handleDocumentTypeChange(type: DocumentType) {
  setFieldValue('tipoDocumento', type);
  setFieldValue('documento', '');
  setDocumentType(type);
}

/**
 * Handler de submit
 */
const onSubmit = handleSubmit((formData) => {
  updateCompanyData({
    razaoSocial: formData.razaoSocial,
    nomeFantasia: formData.nomeFantasia,
    tipoDocumento: formData.tipoDocumento,
    documento: formData.documento,
  });

  updateContactData({
    celular: formData.celular,
    email: formData.email,
    telefone: formData.telefone || '',
  });

  nextStep();
});
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Header da etapa -->
    <div class="text-center mb-8">
      <p class="text-brand-primary font-medium text-sm mb-2">
        Etapa 2 de 4 - Dados da Empresa
      </p>
      <h1 class="text-2xl lg:text-3xl font-bold text-brand-action mb-3">
        Configuração Inicial
      </h1>
      <p class="text-gray-500 text-sm max-w-md mx-auto">
        Configure sua empresa para começar a usar o sistema
      </p>
    </div>

    <form @submit.prevent="onSubmit" class="space-y-8">
      <!-- Seção: Dados da Empresa -->
      <section>
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <SegmentIcons icon="building" size="sm" />
          </div>
          <h2 class="text-lg font-semibold text-brand-action">Dados da Empresa</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Razão Social -->
          <BaseInput
            v-model="razaoSocial"
            label="Razão Social"
            placeholder="Digite a razão social"
            :error="submitCount > 0 ? errors.razaoSocial : ''"
          />

          <!-- Nome Fantasia -->
          <BaseInput
            v-model="nomeFantasia"
            label="Nome Fantasia"
            placeholder="Digite o nome fantasia"
            :error="submitCount > 0 ? errors.nomeFantasia : ''"
          />

          <!-- Documento (CNPJ/CPF) -->
          <div class="space-y-1">
            <label class="block text-xs font-medium text-gray-700">Documento</label>
            <div class="flex gap-2">
              <!-- Seletor de tipo -->
              <div class="relative">
                <select
                  :value="tipoDocumento"
                  @change="handleDocumentTypeChange(($event.target as HTMLSelectElement).value as DocumentType)"
                  class="h-full px-3 py-2 border border-gray-300 rounded-md bg-white text-sm text-gray-700 focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary cursor-pointer appearance-none pr-8"
                >
                  <option value="CNPJ">CNPJ</option>
                  <option value="CPF">CPF</option>
                </select>
                <svg class="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>

              <!-- Input do documento -->
              <div class="flex-1">
                <BaseInput
                  v-model="documento"
                  type="text"
                  :placeholder="tipoDocumento === 'CNPJ' ? 'XX.XXX.XXX/XXXX-XX' : 'XXX.XXX.XXX-XX'"
                  :mask="documentMask"
                  :error="submitCount > 0 ? errors.documento : ''"
                />
              </div>
            </div>
          </div>

          <!-- Segmento (readonly) -->
          <div class="space-y-1">
            <label class="block text-xs font-medium text-gray-700">Seguimento</label>
            <div class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-md bg-gray-50">
              <SegmentIcons v-if="selectedSegment" :icon="selectedSegment.icon" size="sm" />
              <span class="text-sm text-gray-700">{{ selectedSegment?.label || 'Não selecionado' }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Seção: Contatos -->
      <section>
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
          </div>
          <h2 class="text-lg font-semibold text-brand-action">Contatos</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Celular -->
          <BaseInput
            v-model="celular"
            type="tel"
            label="Celular"
            placeholder="(XX) X.XXXX-XXXX"
            mask="(##) #.####-####"
            :error="submitCount > 0 ? errors.celular : ''"
          />

          <!-- E-mail -->
          <BaseInput
            v-model="email"
            type="email"
            label="E-mail"
            placeholder="empresa@empresa.com"
            :error="submitCount > 0 ? errors.email : ''"
          />

          <!-- Telefone -->
          <BaseInput
            v-model="telefone"
            type="tel"
            label="Telefone"
            placeholder="(XX) XXXX-XXXX"
            mask="(##) ####-####"
            :error="submitCount > 0 ? errors.telefone : ''"
          />
        </div>
      </section>

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
