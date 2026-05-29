<script setup lang="ts">
/**
 * @component CompanyStep
 * @description Tela de dados da empresa (Step 2).
 */
import { computed } from 'vue';

// Ícones
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { Building2, Phone, ArrowLeft, ArrowRight } from 'lucide-vue-next';

import { useCompanyForm } from '../../composables/useEmpresaForm';
import { useOnboarding } from '../../composables/useOnboarding';
import { getSegmentById } from '../../constants/segments';
import { TIPO_DOCUMENTO } from '@/shared/constants/documents.constants';
import type { DocumentType } from '../../types/onboarding.types';

// Componentes Base e Negócio
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';
import SelectInput from '../form/SelectInput.vue';

const { onboardingData, previousStep } = useOnboarding();

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
} = useCompanyForm();

const selectedSegment = computed(() => {
  if (!onboardingData.company.segmento) return null;
  return getSegmentById(onboardingData.company.segmento);
});

function changeSelect(document: string) {
  handleDocumentTypeChange(document as DocumentType);
}
</script>

<template>
  <div>
    <form @submit.prevent="onSubmit" class="space-y-8">
      <section>
        <div class="flex items-center gap-3 mb-6">
          <div
            class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600"
          >
            <LucideIcon :icon="Building2" />
          </div>
          <h2 class="text-lg font-semibold text-brand-action">Dados da Empresa</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <BaseInput
            v-model="razaoSocial"
            label="Razão Social"
            placeholder="Digite a razão social"
            :required="true"
            :error="submitCount > 0 ? errors.razaoSocial : ''"
          />
          <BaseInput
            v-model="nomeFantasia"
            label="Nome Fantasia"
            placeholder="Digite o nome fantasia"
            :error="submitCount > 0 ? errors.nomeFantasia : ''"
          />
          <div class="space-y-1">
            <label class="block text-xs font-medium text-gray-700"
              >Documento <span class="text-red-600">*</span></label
            >
            <div class="flex gap-2">
              <SelectInput :options="TIPO_DOCUMENTO" @select="changeSelect" />
              <div class="flex-1">
                <BaseInput
                  v-model="documento"
                  :placeholder="tipoDocumento === 'CNPJ' ? 'XX.XXX.XXX/XXXX-XX' : 'XXX.XXX.XXX-XX'"
                  :required="true"
                  :mask="tipoDocumento === 'CNPJ' ? '##.###.###/####-##' : '###.###.###-##'"
                  :error="submitCount > 0 ? errors.documento : ''"
                />
              </div>
            </div>
          </div>
          <div class="space-y-1">
            <label class="block text-xs font-medium text-gray-700">Segmento</label>
            <div
              class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-md bg-gray-50"
            >
              <SegmentIcons v-if="selectedSegment" :icon="selectedSegment.icon" size="sm" />
              <span class="text-sm text-gray-700">{{
                selectedSegment?.label || 'Não selecionado'
              }}</span>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div class="flex items-center gap-3 mb-6">
          <div
            class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600"
          >
            <LucideIcon :icon="Phone" />
          </div>
          <h2 class="text-lg font-semibold text-brand-action">Contatos</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <BaseInput
            v-model="celular"
            type="tel"
            label="Celular"
            placeholder="(XX) X.XXXX-XXXX"
            :required="true"
            mask="(##) #.####-####"
            :error="submitCount > 0 ? errors.celular : ''"
          />
          <BaseInput
            v-model="email"
            type="email"
            label="E-mail"
            placeholder="empresa@empresa.com"
            :required="true"
            :error="submitCount > 0 ? errors.email : ''"
          />
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

      <div class="flex gap-4 pt-4">
        <BaseButton
          type="button"
          variant="secondary"
          size="lg"
          class="flex-1"
          @click="previousStep"
        >
          <LucideIcon :icon="ArrowLeft" />
          Voltar
        </BaseButton>
        <BaseButton type="submit" size="lg" class="flex-1">
          Salvar
          <LucideIcon :icon="ArrowRight" />
        </BaseButton>
      </div>
    </form>
  </div>
</template>
