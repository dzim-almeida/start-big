<script setup lang="ts">
/**
 * ===========================================================================
 * ARQUIVO: ClientFormModal.vue
 * MODULO: Clientes
 * DESCRICAO: Modal para cadastro e edicao de clientes (PF e PJ).
 * ===========================================================================
 */
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseTab from '@/shared/components/ui/BaseTab/BaseTab.vue';
import AddressForm from '@/shared/components/commons/AddressForm/AddressForm.vue';

// Importa composable unificado
import { useClientForm, TABS_CLIENTE, GENERO_OPTIONS } from '../../composables/useClientForm';
import type { Cliente } from '../../types/clientes.types';

interface Props {
  isOpen: boolean;
  cliente?: Cliente | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
}>();

const {
  formCommon,
  formPF,
  formPJ,
  enderecos,
  tipoCliente,
  isEditMode,
  modalTitle,
  modalSubtitle,
  submitButtonText,
  apiError,
  isPending,
  handleSubmit,
  handleClose
} = useClientForm(props, emit);

</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="modalTitle"
    :subtitle="modalSubtitle"
    size="xl"
    @close="handleClose"
  >
    <!-- Tipo de Cliente Tabs -->
    <div class="mb-6">
      <BaseTab
        :tabs="TABS_CLIENTE"
        v-model="tipoCliente"
        :class="{ 'pointer-events-none opacity-60': isEditMode }"
      />
      <p v-if="isEditMode" class="text-xs text-zinc-400 mt-1">
        O tipo do cliente não pode ser alterado
      </p>
    </div>

    <!-- Erro da API -->
    <div
      v-if="apiError"
      class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700"
    >
      {{ apiError }}
    </div>

    <!-- Single Form -->
    <form class="space-y-6" @submit.prevent="handleSubmit">
      
      <!-- Seção Específica (PF ou PJ) -->
      <div v-if="tipoCliente === 'PF'" class="space-y-4">
        <h4 class="text-sm font-semibold text-zinc-700 border-b border-zinc-200 pb-2">
          Dados Pessoais
        </h4>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <BaseInput
            v-model="formPF.nome"
            label="Nome Completo"
            placeholder="Digite o nome completo"
            required
          />
          <BaseInput
            v-model="formPF.cpf"
            label="CPF"
            placeholder="000.000.000-00"
            mask="###.###.###-##"
            required
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <BaseInput v-model="formPF.rg" label="RG" placeholder="00.000.000-0" />
          <BaseSelect
            v-model="formPF.genero"
            label="Gênero"
            placeholder="Selecione"
            :options="GENERO_OPTIONS"
          />
          <BaseInput
            v-model="formPF.data_nascimento"
            label="Data de Nascimento"
            type="text"
            placeholder="DD/MM/AAAA"
            mask="##/##/####"
          />
        </div>
      </div>

      <div v-else class="space-y-4">
        <h4 class="text-sm font-semibold text-zinc-700 border-b border-zinc-200 pb-2">
          Dados da Empresa
        </h4>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <BaseInput
            v-model="formPJ.razao_social"
            label="Razão Social"
            placeholder="Digite a razão social"
            required
          />
          <BaseInput
            v-model="formPJ.nome_fantasia"
            label="Nome Fantasia"
            placeholder="Digite o nome fantasia"
            required
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <BaseInput
            v-model="formPJ.cnpj"
            label="CNPJ"
            placeholder="00.000.000/0000-00"
            mask="##.###.###/####-##"
            required
          />
          <BaseInput
            v-model="formPJ.responsavel"
            label="Responsável"
            placeholder="Nome do responsável"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <BaseInput
            v-model="formPJ.ie"
            label="Inscrição Estadual"
            placeholder="000.000.000.000"
          />
          <BaseInput
            v-model="formPJ.im"
            label="Inscrição Municipal"
            placeholder="000.000.000.000"
          />
          <BaseInput
            v-model="formPJ.regime_tributario"
            label="Regime Tributário"
            placeholder="Ex: Simples Nacional"
          />
        </div>
      </div>

      <!-- Seção Comum: Contato -->
      <div class="space-y-4">
        <h4 class="text-sm font-semibold text-zinc-700 border-b border-zinc-200 pb-2">Contato</h4>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <BaseInput
            v-model="formCommon.email"
            label="E-mail"
            type="email"
            placeholder="email@exemplo.com"
          />
          <BaseInput
            v-model="formCommon.celular"
            label="Celular"
            placeholder="(00) 00000-0000"
            mask="(##) #####-####"
          />
          <BaseInput
            v-model="formCommon.telefone"
            label="Telefone"
            placeholder="(00) 0000-0000"
            mask="(##) ####-####"
          />
        </div>
      </div>

      <!-- Seção Comum: Endereço -->
      <!-- AddressForm usa a mesma prop para PF e PJ, pois 'enderecos' agora é unificado -->
      <AddressForm v-model="enderecos" :max-enderecos="3" />

      <!-- Seção Comum: Observações -->
      <div class="space-y-4">
        <h4 class="text-sm font-semibold text-zinc-700 border-b border-zinc-200 pb-2">
          Observações
        </h4>
        <textarea
          v-model="formCommon.observacoes"
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
          rows="3"
          placeholder="Observações adicionais sobre o cliente (opcional)"
        ></textarea>
      </div>
    </form>

    <!-- Footer -->
    <template #footer>
      <div class="flex justify-end gap-3">
        <BaseButton type="button" variant="secondary" :disabled="isPending" @click="handleClose">
          Cancelar
        </BaseButton>
        <BaseButton type="button" :is-loading="isPending" @click="handleSubmit">
          {{ submitButtonText }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
