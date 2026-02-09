<script setup lang="ts">
/**
 * @component EmpresaForm
 * @description Formulário principal de dados da empresa
 * Usa provide/inject pattern com VeeValidate
 * Todas as sections injetam context diretamente
 */

import { Building, Save, Globe } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

// Section Components
import IdentificationSection from './form/IdentificationSection.vue';
import AddressSection from './form/AddressSection.vue';
import TaxDataSection from './form/TaxDataSection.vue';
import EmissaoSection from './form/EmissaoSection.vue';
import CertificateSection from './form/CertificateSection.vue';
import ContactSection from './form/ContactSection.vue';

import { useEmpresaFormProvider } from '../composables/useEmpresaFormProvider';

// =============================================
// Provider Setup
// =============================================

// Setup provider - fornece context para todas as sections
const {
  // Fields
  is_cnpj,
  fiscal_settings,

  // State
  apiError,
  isLoading,
  isPending,
  isDirty,

  // Actions
  onSubmit,
} = useEmpresaFormProvider();
</script>

<template>
  <div class="space-y-6">
    <!-- Error Banner -->
    <div
      v-if="apiError"
      class="p-4 bg-red-50 border border-red-200 rounded-lg"
    >
      <p class="text-sm text-red-600">{{ apiError }}</p>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="flex flex-col items-center justify-center py-20 bg-white rounded-xl shadow-sm border border-gray-100"
    >
      <span class="loading loading-spinner loading-lg text-brand-primary mb-4"></span>
      <p class="text-gray-500 font-medium animate-pulse">Carregando informações...</p>
    </div>

    <form v-else class="space-y-8 animate-in fade-in duration-500" @submit.prevent="onSubmit">
      <!-- Header Card -->
      <div
        class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-start justify-between"
      >
        <div>
          <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Building class="text-brand-primary" :size="24" />
            Dados da Organização
          </h2>
          <p class="text-sm text-gray-500 mt-1">
            Mantenha os dados da sua empresa sempre atualizados para emissão de documentos.
          </p>
        </div>
        <div class="hidden md:block">
          <span
            class="px-3 py-1 bg-brand-primary-light text-brand-primary text-xs font-bold uppercase rounded-full tracking-wide"
          >
            {{ is_cnpj ? 'Empresa Verificada' : 'Cadastro Incompleto' }}
          </span>
          <span
            v-if="fiscal_settings"
            class="ml-2 px-3 py-1 text-xs font-bold uppercase rounded-full tracking-wide border"
            :class="
              fiscal_settings.ambiente_emissao === 1
                ? 'bg-red-50 text-red-600 border-red-200'
                : 'bg-blue-50 text-blue-600 border-blue-200'
            "
          >
            <Globe :size="12" class="inline mb-0.5 mr-1" />
            {{ fiscal_settings.ambiente_emissao === 1 ? 'Produção' : 'Homologação' }}
          </span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Left Column: Forms -->
        <div class="lg:col-span-2 space-y-8">
          <!-- Todas as sections injetam context via useEmpresaForm() -->
          <IdentificationSection />
          <AddressSection />
          <TaxDataSection />
          <EmissaoSection />
          <CertificateSection />
          <ContactSection />
        </div>

        <!-- Right Column: Actions -->
        <div class="space-y-6">
          <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 sticky top-6">
            <h3 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Ações</h3>
            <p class="text-sm text-gray-500 mb-6 leading-relaxed">
              Ao salvar, as informações serão atualizadas em todos os orçamentos e ordens de
              serviço futuros.
            </p>
            <BaseButton
              type="submit"
              variant="primary"
              :loading="isPending"
              :disabled="!isDirty"
              class="w-full justify-center py-3 text-sm font-bold shadow-brand-primary-light/20 shadow-lg hover:shadow-brand-primary-light/30 transition-all transform active:scale-95"
            >
              <Save :size="18" class="mr-2" />
              Salvar Alterações
            </BaseButton>
            <div class="mt-4 pt-4 border-t border-gray-100 text-center">
              <span class="text-xs text-gray-400">Última atualização: Hoje</span>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>
