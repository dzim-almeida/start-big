<script setup lang="ts">
/**
 * @component AddressForm
 * @description Componente reutilizável para formulário de endereço.
 * Pode ser usado em cadastro de clientes, funcionários, fornecedores, etc.
 * Suporta múltiplos endereços com botão de adicionar/remover.
 */

import { ref, watch } from 'vue';
import { Plus, Trash2, MapPin } from 'lucide-vue-next';
import BaseInput from '../../ui/BaseInput/BaseInput.vue';
import BaseSelect from '../../ui/BaseSelect/BaseSelect.vue';
import BaseButton from '../../ui/BaseButton/BaseButton.vue';

// Estados brasileiros
const ESTADOS_BRASIL = [
  { value: 'AC', label: 'Acre' },
  { value: 'AL', label: 'Alagoas' },
  { value: 'AP', label: 'Amapá' },
  { value: 'AM', label: 'Amazonas' },
  { value: 'BA', label: 'Bahia' },
  { value: 'CE', label: 'Ceará' },
  { value: 'DF', label: 'Distrito Federal' },
  { value: 'ES', label: 'Espírito Santo' },
  { value: 'GO', label: 'Goiás' },
  { value: 'MA', label: 'Maranhão' },
  { value: 'MT', label: 'Mato Grosso' },
  { value: 'MS', label: 'Mato Grosso do Sul' },
  { value: 'MG', label: 'Minas Gerais' },
  { value: 'PA', label: 'Pará' },
  { value: 'PB', label: 'Paraíba' },
  { value: 'PR', label: 'Paraná' },
  { value: 'PE', label: 'Pernambuco' },
  { value: 'PI', label: 'Piauí' },
  { value: 'RJ', label: 'Rio de Janeiro' },
  { value: 'RN', label: 'Rio Grande do Norte' },
  { value: 'RS', label: 'Rio Grande do Sul' },
  { value: 'RO', label: 'Rondônia' },
  { value: 'RR', label: 'Roraima' },
  { value: 'SC', label: 'Santa Catarina' },
  { value: 'SP', label: 'São Paulo' },
  { value: 'SE', label: 'Sergipe' },
  { value: 'TO', label: 'Tocantins' },
];

interface EnderecoForm {
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;
}

interface Props {
  maxEnderecos?: number;
  required?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  maxEnderecos: 5,
  required: false,
});

const enderecos = defineModel<EnderecoForm[]>({ default: [] });

const loadingCep = ref<number | null>(null);

function createEmptyEndereco(): EnderecoForm {
  return {
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
  };
}

// Inicializar com um endereço vazio se não houver nenhum
watch(
  enderecos,
  (value) => {
    if (!value || value.length === 0) {
      enderecos.value = [createEmptyEndereco()];
    }
  },
  { immediate: true }
);

function addEndereco() {
  if (enderecos.value.length < props.maxEnderecos) {
    enderecos.value.push(createEmptyEndereco());
  }
}

function removeEndereco(index: number) {
  if (enderecos.value.length > 1) {
    enderecos.value.splice(index, 1);
  }
}

async function buscarCep(index: number) {
  const endereco = enderecos.value[index];
  const cep = endereco.cep.replace(/\D/g, '');

  if (cep.length !== 8) return;

  loadingCep.value = index;

  try {
    const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
    const data = await response.json();

    if (!data.erro) {
      enderecos.value[index] = {
        ...endereco,
        logradouro: data.logradouro || '',
        bairro: data.bairro || '',
        cidade: data.localidade || '',
        estado: data.uf || '',
      };
    }
  } catch {
    // Silently fail - user can fill manually
  } finally {
    loadingCep.value = null;
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header com botão de adicionar -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <MapPin :size="18" class="text-zinc-500" />
        <span class="text-sm font-semibold text-zinc-700">Endereços</span>
        <span v-if="required" class="text-red-600 text-xs">*</span>
      </div>
      <BaseButton
        v-if="enderecos.length < maxEnderecos"
        type="button"
        variant="secondary"
        size="sm"
        @click="addEndereco"
      >
        <Plus :size="16" />
        Adicionar
      </BaseButton>
    </div>

    <!-- Lista de Endereços -->
    <div
      v-for="(endereco, index) in enderecos"
      :key="index"
      class="p-4 bg-zinc-50 rounded-xl border border-zinc-200 space-y-4"
    >
      <!-- Header do Endereço -->
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          Endereço {{ index + 1 }}
        </span>
        <button
          v-if="enderecos.length > 1"
          type="button"
          class="text-red-500 hover:text-red-700 transition-colors p-1"
          @click="removeEndereco(index)"
        >
          <Trash2 :size="16" />
        </button>
      </div>

      <!-- Linha 1: CEP -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <BaseInput
          v-model="endereco.cep"
          label="CEP"
          placeholder="00000-000"
          mask="#####-###"
          :required="required"
          @blur="buscarCep(index)"
        />
      </div>

      <!-- Linha 2: Logradouro + Número -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="md:col-span-3">
          <BaseInput
            v-model="endereco.logradouro"
            label="Logradouro"
            placeholder="Rua, Avenida, etc."
            :required="required"
            :disabled="loadingCep === index"
          />
        </div>
        <BaseInput
          v-model="endereco.numero"
          label="Número"
          placeholder="Nº"
          :required="required"
        />
      </div>

      <!-- Linha 3: Complemento + Bairro -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BaseInput
          v-model="endereco.complemento"
          label="Complemento"
          placeholder="Apto, Sala, etc. (opcional)"
        />
        <BaseInput
          v-model="endereco.bairro"
          label="Bairro"
          placeholder="Bairro"
          :required="required"
          :disabled="loadingCep === index"
        />
      </div>

      <!-- Linha 4: Cidade + Estado -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BaseInput
          v-model="endereco.cidade"
          label="Cidade"
          placeholder="Cidade"
          :required="required"
          :disabled="loadingCep === index"
        />
        <BaseSelect
          v-model="endereco.estado"
          label="Estado"
          placeholder="Selecione o estado"
          :options="ESTADOS_BRASIL"
          :required="required"
          :disabled="loadingCep === index"
        />
      </div>
    </div>

    <!-- Mensagem de limite -->
    <p v-if="enderecos.length >= maxEnderecos" class="text-xs text-zinc-400 text-center">
      Limite de {{ maxEnderecos }} endereços atingido
    </p>
  </div>
</template>
