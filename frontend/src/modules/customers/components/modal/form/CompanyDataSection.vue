<script setup lang="ts">
/**
 * @component CompanyDataSection
 * @description Form section for PJ (company) customer data
 */

import { computed, watch } from 'vue';
import { Building2, Search } from 'lucide-vue-next';
import { cnpj as validadorCnpj } from 'cpf-cnpj-validator';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useCustomerForm } from '@/modules/customers/composables/modal/context/useCustomerForm.context';
import { REGIME_TRIBUTARIO_OPTIONS } from '@/modules/enterprise/constants/empresa.constants';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';

const configStore = useConfiguracoesStore();

// =============================================
// Props
// =============================================

interface Props {
  disabled?: boolean;
}

defineProps<Props>();

// =============================================
// Form Fields
// =============================================

const {
  razao_social,
  nome_fantasia,
  cnpj,
  ie,
  im,
  regime_tributario,
  responsavel,
  errors,
  submitCount,
  isConsultingCNPJ,
  consultarReceita,
  avisoCnpj,
  limparAvisoCnpj,
  isCreateMode,
} = useCustomerForm();

// =============================================
// Busca na Receita pelo CNPJ
// =============================================

const cnpjDigitos = computed(() => (cnpj.value ?? '').replace(/\D/g, ''));

/**
 * CNPJ completo E com o dígito verificador certo (Spec 02, D3). CNPJ digitado
 * errado não gasta consulta e não mostra "não encontrado" por cima do erro do
 * próprio campo.
 */
const cnpjValido = computed(
  () => cnpjDigitos.value.length === 14 && validadorCnpj.isValid(cnpjDigitos.value),
);

/**
 * No cadastro NOVO, buscar sozinho quando o CNPJ fica completo e válido — como
 * em Dados da Empresa. Na edição, só pelo botão: abrir um cliente salvo não
 * pode sobrescrever o que alguém já corrigiu à mão.
 */
watch(cnpjDigitos, (digitos, anterior) => {
  if (digitos !== anterior) limparAvisoCnpj();                   // o aviso era do CNPJ anterior
  if (!isCreateMode.value || !cnpjValido.value || digitos === anterior) return;
  consultarReceita(digitos);
});
</script>

<template>
  <section>
    <!-- Section Header -->
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-brand-primary-light rounded-xl flex items-center justify-center text-brand-primary"
      >
        <LucideIcon :icon="Building2" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Dados da Empresa</h3>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <!-- Row 1: Razao Social, Nome Fantasia -->
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="razao_social"
          label="Razão Social"
          placeholder="Digite a razão social"
          :required="true"
          :error="submitCount > 0 ? errors.razao_social : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="nome_fantasia"
          label="Nome Fantasia"
          placeholder="Digite o nome fantasia"
          :required="true"
          :error="submitCount > 0 ? errors.nome_fantasia : ''"
          :disabled="disabled"
        />
      </div>

      <!-- Row 2: CNPJ, Responsavel -->
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="cnpj"
          label="CNPJ"
          placeholder="00.000.000/0000-00"
          mask="##.###.###/####-##"
          :required="configStore.exigirCnpjPj"
          :error="submitCount > 0 ? errors.cnpj : ''"
          :disabled="disabled || isConsultingCNPJ"
        />
        <div
          v-if="isConsultingCNPJ"
          class="mt-1.5 text-xs text-brand-primary animate-pulse"
        >
          Consultando Receita Federal...
        </div>
        <!-- Desabilitado com dígito verificador errado (Spec 02, D3). -->
        <button
          v-else-if="cnpjDigitos.length === 14 && !disabled"
          type="button"
          class="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline disabled:opacity-50 disabled:no-underline disabled:cursor-not-allowed"
          :disabled="!cnpjValido"
          @click="consultarReceita(cnpjDigitos)"
        >
          <Search :size="11" />
          Buscar dados na Receita
        </button>
        <!-- Aviso de duplicidade: fica visível até o CNPJ mudar (Spec 02, D4/D6).
             aria-live avisa o leitor de tela sem roubar o foco. -->
        <p aria-live="polite" class="text-xs text-amber-700">
          <!-- A margem fica no texto: vazio, o parágrafo não ocupa espaço na tela. -->
          <span v-if="avisoCnpj?.tipo === 'duplicado'" class="block mt-1.5">
            Já existe um cliente com este CNPJ: <strong>{{ avisoCnpj.nomeCliente }}</strong>.
            Salvar vai dar erro de duplicidade.
          </span>
        </p>
      </div>
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="responsavel"
          label="Responsável"
          placeholder="Nome do responsável"
          :error="submitCount > 0 ? errors.responsavel : ''"
          :disabled="disabled"
        />
      </div>

      <!-- Row 3: IE, IM, Regime Tributario -->
      <div class="col-span-12 md:col-span-4">
        <BaseInput
          v-model="ie"
          label="Inscrição Estadual"
          placeholder="000.000.000.000"
          :required="configStore.exigirIePj"
          :error="submitCount > 0 ? errors.ie : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-4">
        <BaseInput
          v-model="im"
          label="Inscrição Municipal"
          placeholder="000.000.000.000"
          :error="submitCount > 0 ? errors.im : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-4">
        <BaseSelect
          v-model="regime_tributario"
          label="Regime Tributário"
          :options="REGIME_TRIBUTARIO_OPTIONS"
          placeholder="Selecione o regime"
          :error="submitCount > 0 ? errors.regime_tributario : ''"
          :disabled="disabled"
        />
      </div>
    </div>
  </section>
</template>
