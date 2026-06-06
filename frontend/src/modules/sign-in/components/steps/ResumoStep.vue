<script setup lang="ts">
/**
 * @component ResumoStep
 * @description Tela de resumo e confirmação dos dados (Passo 4).
 */
import { computed } from 'vue';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { AlertCircle, Lightbulb, ArrowLeft, CheckCircle2 } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useSignIn } from '../../composables/useSignIn';
import { useSetup } from '../../composables/useSetup';
import { getSegmentById } from '../../constants/segments';
import SegmentIcons from '../icons/SegmentIcons.vue';

const { confirmSetup, isPending, apiError } = useSetup();
const { signInData, previousStep } = useSignIn();

const selectedSegment = computed(() => {
  if (!signInData.loja.segmento) return null;
  return getSegmentById(signInData.loja.segmento);
});

const segmentResumoTip = computed(() => {
  if (!selectedSegment.value) return 'Outros';
  return selectedSegment.value.label;
});

const isPF = computed(() => signInData.responsavel.tipoPessoa === 'PF');

interface ResumoField {
  label: string;
  value: string;
  hideIfEmpty?: boolean;
}

const lojaFields = computed<ResumoField[]>(() => [
  { label: 'Nome da Loja', value: signInData.loja.nomeLoja },
  { label: 'Segmento', value: selectedSegment.value?.label || '' },
  { label: 'Celular', value: signInData.loja.celular },
  { label: 'E-mail da Loja', value: signInData.loja.emailLoja },
  { label: 'Telefone', value: signInData.loja.telefone, hideIfEmpty: true },
]);

const enderecoFields = computed<ResumoField[]>(() => [
  { label: 'CEP', value: signInData.loja.cep },
  { label: 'Logradouro', value: signInData.loja.logradouro },
  { label: 'Número', value: signInData.loja.numero || 'S/N' },
  { label: 'Bairro', value: signInData.loja.bairro },
  { label: 'Complemento', value: signInData.loja.complemento, hideIfEmpty: true },
  { label: 'Cidade', value: signInData.loja.cidade },
  { label: 'Estado', value: signInData.loja.estado },
]);

const responsavelFields = computed<ResumoField[]>(() => {
  const fields: ResumoField[] = [
    { label: 'Tipo', value: isPF.value ? 'Pessoa Física' : 'Pessoa Jurídica' },
  ];

  if (isPF.value) {
    fields.push(
      { label: 'Nome Completo', value: signInData.responsavel.nomeResponsavel },
      { label: 'CPF', value: signInData.responsavel.cpf },
      { label: 'RG', value: signInData.responsavel.rg, hideIfEmpty: true },
      { label: 'Gênero', value: signInData.responsavel.genero, hideIfEmpty: true },
      { label: 'Data de Nascimento', value: signInData.responsavel.dataNascimento, hideIfEmpty: true },
    );
  } else {
    fields.push(
      { label: 'Razão Social', value: signInData.responsavel.razaoSocial },
      { label: 'CNPJ', value: signInData.responsavel.cnpj },
      { label: 'Nome Fantasia', value: signInData.responsavel.nomeFantasiaPJ, hideIfEmpty: true },
      { label: 'Inscrição Estadual', value: signInData.responsavel.inscricaoEstadual, hideIfEmpty: true },
      { label: 'Inscrição Municipal', value: signInData.responsavel.inscricaoMunicipal, hideIfEmpty: true },
      { label: 'Regime Tributário', value: signInData.responsavel.regimeTributario, hideIfEmpty: true },
      { label: 'Responsável', value: signInData.responsavel.nomeResponsavel },
    );
  }

  // Contato
  if (signInData.responsavel.celularResponsavel) {
    fields.push({ label: 'Celular', value: signInData.responsavel.celularResponsavel });
  }
  if (signInData.responsavel.emailResponsavel) {
    fields.push({ label: 'E-mail', value: signInData.responsavel.emailResponsavel });
  }

  return fields;
});

const acessoFields = computed<ResumoField[]>(() => [
  { label: 'Nome de Exibição', value: signInData.acesso.nomeUsuario },
  { label: 'E-mail de Acesso', value: signInData.acesso.email },
  { label: 'Senha', value: '••••••••' },
]);
</script>

<template>
  <div>
    <!-- Erro da API -->
    <div
      v-if="apiError"
      class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3"
    >
      <div
        class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center shrink-0 text-red-600"
      >
        <LucideIcon :icon="AlertCircle" />
      </div>
      <p class="text-sm text-red-700">{{ apiError }}</p>
    </div>

    <!-- Dica do segmento -->
    <div
      v-if="selectedSegment"
      class="mb-4 p-3 bg-blue-50 border border-blue-100 rounded-lg flex items-center gap-2"
    >
      <SegmentIcons :icon="selectedSegment.icon" :size="24" class="text-brand-primary shrink-0" />
      <p class="mx-2 text-xs text-brand-primary">
        O sistema será personalizado para <strong>{{ segmentResumoTip }}</strong>, mas você poderá ajustar as configurações a qualquer momento.
      </p>
    </div>

    <div class="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
      <!-- Loja -->
      <div class="p-5 border-b border-gray-100">
        <p class="text-xs font-semibold text-brand-primary mb-3 uppercase tracking-wider">Dados da Loja</p>
        <div class="grid grid-cols-2 gap-4">
          <template v-for="field in lojaFields" :key="field.label">
            <div v-if="!field.hideIfEmpty || field.value">
              <p class="text-xs text-gray-500 mb-0.5">{{ field.label }}</p>
              <p class="font-medium text-brand-action text-sm">{{ field.value }}</p>
            </div>
          </template>
        </div>
      </div>

      <!-- Endereço -->
      <div class="p-5 border-b border-gray-100">
        <p class="text-xs font-semibold text-brand-primary mb-3 uppercase tracking-wider">Endereço</p>
        <div class="grid grid-cols-2 gap-4">
          <template v-for="field in enderecoFields" :key="field.label">
            <div v-if="!field.hideIfEmpty || field.value">
              <p class="text-xs text-gray-500 mb-0.5">{{ field.label }}</p>
              <p class="font-medium text-brand-action text-sm">{{ field.value }}</p>
            </div>
          </template>
        </div>
      </div>

      <!-- Responsável -->
      <div class="p-5 border-b border-gray-100">
        <p class="text-xs font-semibold text-brand-primary mb-3 uppercase tracking-wider">Responsável</p>
        <div class="grid grid-cols-2 gap-4">
          <template v-for="field in responsavelFields" :key="field.label">
            <div v-if="!field.hideIfEmpty || field.value">
              <p class="text-xs text-gray-500 mb-0.5">{{ field.label }}</p>
              <p class="font-medium text-brand-action text-sm">{{ field.value }}</p>
            </div>
          </template>
        </div>
      </div>

      <!-- Dados de Acesso -->
      <div class="p-5">
        <p class="text-xs font-semibold text-brand-primary mb-3 uppercase tracking-wider">Dados de Acesso</p>
        <div class="grid grid-cols-2 gap-4">
          <template v-for="field in acessoFields" :key="field.label">
            <div>
              <p class="text-xs text-gray-500 mb-0.5">{{ field.label }}</p>
              <p class="font-medium text-brand-action text-sm">{{ field.value }}</p>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Dica -->
    <div class="mt-6 p-4 bg-amber-50 border border-amber-100 rounded-xl flex items-start gap-3">
      <div
        class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center shrink-0 text-amber-600"
      >
        <LucideIcon :icon="Lightbulb" />
      </div>
      <p class="text-sm text-amber-800">
        Ao confirmar, o sistema criará sua loja, usuário administrador e
        <strong>cargo Master</strong> com permissões totais.
      </p>
    </div>

    <!-- Botões -->
    <div class="flex gap-4 mt-8">
      <BaseButton
        type="button"
        variant="secondary"
        size="lg"
        class="flex-1"
        :disabled="isPending"
        @click="previousStep"
      >
        <LucideIcon :icon="ArrowLeft" />
        Voltar
      </BaseButton>
      <BaseButton size="lg" class="flex-1" :is-loading="isPending" @click="confirmSetup">
        <LucideIcon :icon="CheckCircle2" />
        Confirmar
      </BaseButton>
    </div>
  </div>
</template>
