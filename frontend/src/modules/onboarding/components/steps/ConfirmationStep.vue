<script setup lang="ts">
/**
 * @component ConfirmationStep
 * @description Tela de confirmação dos dados (Step 4).
 * Exibe um resumo de todos os dados inseridos antes da submissão final.
 */

import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useMutation } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import BaseButton from '@/shared/components/BaseButton/BaseButton.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';
import { useOnboarding } from '../../composables/useOnboarding';
import { useToast } from '@/shared/composables/useToast';
import { createCompany, cleanDocument, cleanPhone } from '../../services/onboarding.service';
import { getSegmentById } from '../../constants/segments';
import type { CreateCompanyRequest, CreateCompanyResponse } from '../../types/onboarding.types';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';

const router = useRouter();
const toast = useToast();
const { onboardingData, previousStep, resetOnboarding } = useOnboarding();
const apiError = ref<string | null>(null);

/**
 * Segmento selecionado
 */
const selectedSegment = computed(() => {
  if (!onboardingData.company.segmento) return null;
  return getSegmentById(onboardingData.company.segmento);
});

/**
 * Mutation para criar empresa
 */
const createCompanyMutation = useMutation<CreateCompanyResponse, AxiosError<ApiError>, CreateCompanyRequest>({
  mutationFn: createCompany,
  onSuccess: () => {
    toast.success(
      'Empresa cadastrada com sucesso!',
      'Sua configuração inicial foi concluída. Bem-vindo ao Start Big!'
    );
    resetOnboarding();
    router.push('/');
  },
  onError: (error) => {
    apiError.value = getErrorMessage(error, 'Erro ao cadastrar empresa');
  },
});

/**
 * Handler de submit final
 */
function handleSubmit() {
  if (!onboardingData.company.segmento) return;

  apiError.value = null;

  const request: CreateCompanyRequest = {
    razao_social: onboardingData.company.razaoSocial,
    nome_fantasia: onboardingData.company.nomeFantasia,
    tipo_documento: onboardingData.company.tipoDocumento,
    documento: cleanDocument(onboardingData.company.documento),
    segmento: onboardingData.company.segmento,
    celular: cleanPhone(onboardingData.contact.celular),
    email: onboardingData.contact.email,
    telefone: onboardingData.contact.telefone ? cleanPhone(onboardingData.contact.telefone) : undefined,
    cep: onboardingData.address.cep.replace(/\D/g, ''),
    logradouro: onboardingData.address.logradouro,
    numero: onboardingData.address.numero,
    complemento: onboardingData.address.complemento || undefined,
    bairro: onboardingData.address.bairro,
    cidade: onboardingData.address.cidade,
    estado: onboardingData.address.estado,
  };

  createCompanyMutation.mutate(request);
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Header da etapa -->
    <div class="text-center mb-8">
      <p class="text-brand-primary font-medium text-sm mb-2">
        Etapa 4 de 4 - Confirmação
      </p>
      <h1 class="text-2xl lg:text-3xl font-bold text-brand-action mb-3">
        Configuração Inicial
      </h1>
      <p class="text-gray-500 text-sm max-w-md mx-auto">
        Configure sua empresa para começar a usar o sistema
      </p>
    </div>

    <!-- Erro da API -->
    <div
      v-if="apiError"
      class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3"
    >
      <div class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
        <svg class="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p class="text-sm text-red-700">{{ apiError }}</p>
    </div>

    <!-- Card de resumo -->
    <div class="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
      <!-- Segmento -->
      <div class="p-6 border-b border-gray-100">
        <p class="text-xs text-gray-500 mb-2">Seguimento</p>
        <div class="flex items-center gap-3">
          <div class="p-2 bg-blue-50 rounded-xl">
            <SegmentIcons v-if="selectedSegment" :icon="selectedSegment.icon" size="md" />
          </div>
          <span class="font-semibold text-brand-action">{{ selectedSegment?.label }}</span>
        </div>
      </div>

      <!-- Dados da Empresa -->
      <div class="p-6 border-b border-gray-100">
        <div class="grid grid-cols-2 gap-6">
          <div>
            <p class="text-xs text-gray-500 mb-1">Razão social</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.company.razaoSocial }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Nome Fantasia</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.company.nomeFantasia }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">{{ onboardingData.company.tipoDocumento }}</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.company.documento }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Contato</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.contact.celular }}</p>
          </div>
        </div>
      </div>

      <!-- Endereço -->
      <div class="p-6">
        <div class="grid grid-cols-2 gap-6">
          <div>
            <p class="text-xs text-gray-500 mb-1">CEP</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.address.cep }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Logradouro/Rua</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.address.logradouro }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Número</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.address.numero }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Bairro</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.address.bairro }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Cidade</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.address.cidade }}</p>
          </div>
          <div v-if="onboardingData.address.complemento">
            <p class="text-xs text-gray-500 mb-1">Complemento</p>
            <p class="font-medium text-brand-action text-sm">{{ onboardingData.address.complemento }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Mensagem informativa -->
    <div class="mt-6 p-4 bg-amber-50 border border-amber-100 rounded-xl flex items-start gap-3">
      <div class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
        <svg class="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>
      <p class="text-sm text-amber-800">
        O sistema será personalizado para
        <strong class="underline">{{ selectedSegment?.label }}</strong>
        com campos e recursos específicos para seu segmento.
      </p>
    </div>

    <!-- Botões de navegação -->
    <div class="flex gap-4 mt-8">
      <BaseButton
        type="button"
        variant="secondary"
        size="lg"
        class="flex-1"
        :disabled="createCompanyMutation.isPending.value"
        @click="previousStep"
      >
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
        </svg>
        Voltar
      </BaseButton>

      <BaseButton
        size="lg"
        class="flex-1"
        :is-loading="createCompanyMutation.isPending.value"
        @click="handleSubmit"
      >
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Salvar
      </BaseButton>
    </div>
  </div>
</template>
