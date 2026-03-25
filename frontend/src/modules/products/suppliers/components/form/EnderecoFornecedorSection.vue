// ============================================================================
// COMPONENTE: EnderecoFornecedorSection (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Formulário de endereço do fornecedor com busca automática por CEP.
// ============================================================================
<script setup lang="ts">
import { ref, watch } from 'vue';
import { MapPin } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useCepQuery } from '@/shared/composables/useCepLookup';
import { ESTADOS_BRASILEIROS } from '@/shared/constants/locations.constants';
import { useFornecedorForm } from '../../composables/useFornecedorForm';

interface Props {
  submitCount: number;
  disabled?: boolean;
}

defineProps<Props>();

const {
  logradouro,
  numero,
  complemento,
  bairro,
  cidade,
  estado,
  cep,
  errors,
} = useFornecedorForm();

const cepRef = ref(cep.value);

watch(cep, (newVal) => {
  cepRef.value = newVal;
});

const { data: cepData, isLoading: cepIsLoading, isError: cepIsError } = useCepQuery(cepRef);

watch(cepData, (data) => {
  if (data) {
    logradouro.value = data.logradouro || '';
    bairro.value = data.bairro || '';
    cidade.value = data.localidade || '';
    estado.value = data.uf || '';
    complemento.value = data.complemento || '';
  }
});
</script>

<template>
  <section>
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600"
      >
        <LucideIcon :icon="MapPin" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Endereço</h3>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <!-- CEP -->
      <div class="col-span-12 md:col-span-3">
        <div class="relative">
          <BaseInput
            v-model="cep"
            label="CEP"
            placeholder="00000-000"
            mask="#####-###"
            :disabled="disabled || cepIsLoading"
            :error="submitCount > 0 ? errors.cep : ''"
          />
          <div v-if="cepIsLoading" class="absolute right-3 top-8">
            <svg class="animate-spin h-4 w-4 text-brand-primary" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        </div>
        <p v-if="cepIsError" class="mt-1 text-xs text-amber-600">CEP não encontrado</p>
      </div>

      <!-- Logradouro -->
      <div class="col-span-12 md:col-span-7">
        <BaseInput
          v-model="logradouro"
          label="Logradouro/Rua"
          placeholder="Digite o logradouro"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.logradouro : ''"
        />
      </div>

      <!-- Numero -->
      <div class="col-span-12 md:col-span-2">
        <BaseInput
          v-model="numero"
          label="Numero"
          placeholder="No"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.numero : ''"
        />
      </div>

      <!-- Complemento -->
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="complemento"
          label="Complemento"
          placeholder="Apto, Sala, etc. (opcional)"
          :disabled="disabled"
        />
      </div>

      <!-- Bairro -->
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="bairro"
          label="Bairro"
          placeholder="Digite o bairro"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.bairro : ''"
        />
      </div>

      <!-- Cidade -->
      <div class="col-span-12 md:col-span-8">
        <BaseInput
          v-model="cidade"
          label="Cidade"
          placeholder="Digite a cidade"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.cidade : ''"
        />
      </div>

      <!-- Estado -->
      <div class="col-span-12 md:col-span-4">
        <BaseSelect
          v-model="estado"
          label="Estado"
          placeholder="Selecione"
          :options="ESTADOS_BRASILEIROS"
          :disabled="disabled"
        />
      </div>
    </div>
  </section>
</template>