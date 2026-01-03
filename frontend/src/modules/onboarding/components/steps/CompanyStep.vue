<script setup lang="ts">
/**
 * @component CompanyStep
 * @description Tela de dados da empresa (Step 2).
 * Formulário com razão social, nome fantasia, documento e contatos.
 */

import { computed } from 'vue';
import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/BaseInput/BaseInput.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';
import { useCompanyForm } from '../../composables/useEmpresaForm';
import { useOnboarding } from '../../composables/useOnboarding';
import { getSegmentById } from '../../constants/segments';
import type { DocumentType } from '../../types/onboarding.types';
import Icons from '../icons/Icons.vue';
import SelectInput from '../commons/SelectInput.vue';

const { onboardingData, previousStep } = useOnboarding();

/**
 * Dados para formulários
 */
const {
  razaoSocial,
  nomeFantasia,
  tipoDocumento,
  documento,
  celular,
  email,
  telefone,
  errors,
  onSubmit,
  submitCount,
  handleDocumentTypeChange,
} = useCompanyForm()

/**
 * Segmento selecionado
 */
const selectedSegment = computed(() => {
  if (!onboardingData.company.segmento) return null;
  return getSegmentById(onboardingData.company.segmento);
});

/**
 * Opções para selecionar no campo documento
 */
const selectDocumentOptions = [
  {
    label: 'CNPJ',
    value: 'CNPJ'
  },
  {
    label: 'CPF',
    value: 'CPF'
  },
];

/**
 * Emit para select
 */
function changeSelect(document: string) {
  handleDocumentTypeChange(document as DocumentType)
}
</script>

<template>
  <div>
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
            :required="true"
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
            <label class="block text-xs font-medium text-gray-700">Documento <span class="text-red-600">*</span></label>
            <div class="flex gap-2">
              <!-- Seletor de tipo -->
              <SelectInput
                :options="selectDocumentOptions"
                @select="changeSelect"
              />
              <!-- Input do documento -->
              <div class="flex-1">
                <BaseInput
                  v-model="documento"
                  type="text"
                  :placeholder="tipoDocumento === 'CNPJ' ? 'XX.XXX.XXX/XXXX-XX' : 'XXX.XXX.XXX-XX'"
                  :required="true"
                  :mask="tipoDocumento === 'CNPJ' ? '##.###.###/####-##' : '###.###.###-##'"
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
          <div class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <Icons icon="phone" />
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
            :required="true"
            mask="(##) #.####-####"
            :error="submitCount > 0 ? errors.celular : ''"
          />

          <!-- E-mail -->
          <BaseInput
            v-model="email"
            type="email"
            label="E-mail"
            placeholder="empresa@empresa.com"
            :required="true"
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
