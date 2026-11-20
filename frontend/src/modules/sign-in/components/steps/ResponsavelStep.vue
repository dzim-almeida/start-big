<script setup lang="ts">
/**
 * @component ResponsavelStep
 * @description Formulário de dados do responsável pelo negócio (Passo 2).
 * Inclui toggle PF/PJ com formulários distintos para cada tipo.
 */

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowLeft, ArrowRight, Info, Cloud } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useResponsavelForm } from '../../composables/useResponsavelForm';
import { useSignIn } from '../../composables/useSignIn';

const {
  tipoPessoa,
  nomeResponsavel,
  cpfField,
  rg,
  genero,
  dataNascimento,
  razaoSocial,
  cnpj,
  nomeFantasiaPJ,
  inscricaoEstadual,
  inscricaoMunicipal,
  regimeTributario,
  celularResponsavel,
  emailResponsavel,
  errors,
  onSubmit,
  submitCount,
  handleTipoPessoaChange,
} = useResponsavelForm();

// documentoTravado = os dados vieram da conta na nuvem (re-login sem backup, LIC-03 §6.6):
// o CPF/CNPJ e o tipo de pessoa não podem ser trocados aqui, só pelo suporte.
const { previousStep, documentoTravado } = useSignIn();

const generoOptions = [
  { value: 'MASCULINO', label: 'Masculino' },
  { value: 'FEMININO', label: 'Feminino' },
  { value: 'OUTRO', label: 'Outro' },
];

const regimeTributarioOptions = [
  { value: 'Simples Nacional', label: 'Simples Nacional' },
  { value: 'Lucro Presumido', label: 'Lucro Presumido' },
  { value: 'Lucro Real', label: 'Lucro Real' },
  { value: 'MEI', label: 'MEI' },
];
</script>

<template>
  <form @submit.prevent="onSubmit">
    <!-- Dica -->
    <div class="p-3 mb-6 bg-blue-50 border border-blue-100 rounded-lg flex items-start gap-2">
      <LucideIcon :icon="Info" size="md" class="text-brand-primary mt-0.5 shrink-0" />
      <p class="text-xs text-brand-primary">
        Cadastre os dados da pessoa responsável pelo negócio. Esses dados serão vinculados
        ao funcionário master do sistema.
      </p>
    </div>
    <!-- Dados vindos da nuvem (quadro 7) -->
    <div v-if="documentoTravado" class="p-3 mb-6 bg-blue-50 border border-blue-100 rounded-lg flex items-start gap-2">
      <LucideIcon :icon="Cloud" size="md" class="text-brand-primary mt-0.5 shrink-0" />
      <p class="text-xs text-brand-primary">
        Estes dados vêm da sua conta na StartBig. Confira e complete o que faltar.
      </p>
    </div>
    <h3 class="text-sm font-semibold text-brand-action mb-4">Dados do Responsável</h3>

    <!-- Toggle PF/PJ -->
    <div class="mb-6">
      <label class="block text-xs font-medium text-gray-700 mb-2">Tipo de Pessoa</label>
      <div class="flex gap-2">
        <button
          type="button"
          class="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all border disabled:opacity-60 disabled:cursor-not-allowed"
          :class="
            tipoPessoa === 'PF'
              ? 'bg-brand-primary text-white border-brand-primary'
              : 'bg-white text-gray-600 border-gray-200 hover:border-brand-primary'
          "
          :disabled="documentoTravado"
          @click="handleTipoPessoaChange('PF')"
        >
          Pessoa Física (PF)
        </button>
        <button
          type="button"
          class="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all border disabled:opacity-60 disabled:cursor-not-allowed"
          :class="
            tipoPessoa === 'PJ'
              ? 'bg-brand-primary text-white border-brand-primary'
              : 'bg-white text-gray-600 border-gray-200 hover:border-brand-primary'
          "
          :disabled="documentoTravado"
          @click="handleTipoPessoaChange('PJ')"
        >
          Pessoa Jurídica (PJ)
        </button>
      </div>
    </div>

    <!-- ===== Formulário PF ===== -->
    <template v-if="tipoPessoa === 'PF'">
      <div class="grid grid-cols-2 gap-4 mb-6">
        <BaseInput
          v-model="nomeResponsavel"
          label="Nome Completo"
          placeholder="Seu nome completo"
          required
          :error="submitCount > 0 ? errors.nomeResponsavel : ''"
        />
        <!-- CPF: travado quando vem da nuvem (D-22, CT-14) -->
        <div class="flex flex-col gap-1">
          <BaseInput
            v-model="cpfField"
            label="CPF"
            placeholder="000.000.000-00"
            mask="###.###.###-##"
            required
            :disabled="documentoTravado"
            :error="submitCount > 0 ? errors.cpf : ''"
          />
          <p v-if="documentoTravado" class="text-[11px] text-gray-500">
            Vem da sua conta StartBig. Para alterar, fale com o suporte.
          </p>
        </div>
        <BaseInput
          v-model="rg"
          label="RG (opcional)"
          placeholder="Número do RG"
          :error="submitCount > 0 ? errors.rg : ''"
        />
        <BaseSelect
          v-model="genero"
          label="Gênero (opcional)"
          placeholder="Selecione"
          :options="generoOptions"
          :error="submitCount > 0 ? errors.genero : ''"
        />
        <BaseDateInput
          v-model="dataNascimento"
          label="Data de Nascimento (opcional)"
          :error="submitCount > 0 ? errors.dataNascimento : ''"
        />
      </div>
    </template>

    <!-- ===== Formulário PJ ===== -->
    <template v-else>
      <h3 class="text-sm font-semibold text-brand-action mb-4">Dados da Empresa</h3>
      <div class="grid grid-cols-2 gap-4 mb-6">
        <BaseInput
          v-model="razaoSocial"
          label="Razão Social"
          placeholder="Razão social da empresa"
          required
          :error="submitCount > 0 ? errors.razaoSocial : ''"
        />
        <!-- CNPJ: travado quando vem da nuvem (D-22, CT-14) -->
        <div class="flex flex-col gap-1">
          <BaseInput
            v-model="cnpj"
            label="CNPJ"
            placeholder="00.000.000/0000-00"
            mask="##.###.###/####-##"
            required
            :disabled="documentoTravado"
            :error="submitCount > 0 ? errors.cnpj : ''"
          />
          <p v-if="documentoTravado" class="text-[11px] text-gray-500">
            Vem da sua conta StartBig. Para alterar, fale com o suporte.
          </p>
        </div>
        <BaseInput
          v-model="nomeFantasiaPJ"
          label="Nome Fantasia (opcional)"
          placeholder="Nome comercial"
          :error="submitCount > 0 ? errors.nomeFantasiaPJ : ''"
        />
        <BaseInput
          v-model="inscricaoEstadual"
          label="Inscrição Estadual (opcional)"
          placeholder="IE"
          :error="submitCount > 0 ? errors.inscricaoEstadual : ''"
        />
        <BaseInput
          v-model="inscricaoMunicipal"
          label="Inscrição Municipal (opcional)"
          placeholder="IM"
          :error="submitCount > 0 ? errors.inscricaoMunicipal : ''"
        />
        <BaseSelect
          v-model="regimeTributario"
          label="Regime Tributário (opcional)"
          placeholder="Selecione"
          :options="regimeTributarioOptions"
          :error="submitCount > 0 ? errors.regimeTributario : ''"
        />
      </div>

      <!-- Separador: Dados do Responsável -->
      <h3 class="text-sm font-semibold text-brand-action mb-4">Dados do Responsável</h3>
      <div class="grid grid-cols-2 gap-4 mb-6">
        <BaseInput
          v-model="nomeResponsavel"
          label="Nome do Responsável"
          placeholder="Nome completo do responsável"
          required
          :error="submitCount > 0 ? errors.nomeResponsavel : ''"
        />
      </div>
    </template>

    <!-- Contato do Responsável (ambos PF/PJ) -->
    <h3 class="text-sm font-semibold text-brand-action mb-4">Contato</h3>
    <div class="grid grid-cols-2 gap-4 mb-6">
      <BaseInput
        v-model="celularResponsavel"
        label="Celular (opcional)"
        placeholder="(00) 0.0000-0000"
        mask="(##) #.####-####"
        :error="submitCount > 0 ? errors.celularResponsavel : ''"
      />
      <BaseInput
        v-model="emailResponsavel"
        type="email"
        label="E-mail (opcional)"
        placeholder="responsavel@email.com"
        :error="submitCount > 0 ? errors.emailResponsavel : ''"
      />
    </div>

    <!-- Botões -->
    <div class="flex gap-4 mt-6">
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
        Próximo
        <LucideIcon :icon="ArrowRight" />
      </BaseButton>
    </div>
  </form>
</template>
