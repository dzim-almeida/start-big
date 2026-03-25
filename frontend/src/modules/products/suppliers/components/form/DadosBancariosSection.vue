// ============================================================================
// COMPONENTE: DadosBancariosSection (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Formulário de dados bancários e observações do fornecedor.
// ============================================================================
<script setup lang="ts">
import { Landmark } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useFornecedorForm } from '../../composables/useFornecedorForm';

interface Props {
  submitCount: number;
  disabled?: boolean;
}

defineProps<Props>();

const {
  banco,
  agencia,
  conta,
  tipo_conta,
  pix,
  errors,
} = useFornecedorForm();

const tipoCcOptions: SelectOption[] = [
  { value: 'CORRENTE', label: 'Conta Corrente' },
  { value: 'POUPANCA', label: 'Conta Poupança' },
];
</script>

<template>
  <section>
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-brand-primary"
      >
        <LucideIcon :icon="Landmark" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Dados Bancários</h3>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="banco"
          label="Banco"
          placeholder="Nome do banco"
          :error="submitCount > 0 ? errors.banco : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-6">
        <BaseSelect
          v-model="tipo_conta"
          label="Tipo de Conta"
          placeholder="Selecione o tipo"
          :options="tipoCcOptions"
          :disabled="disabled"
        />
      </div>

      <div class="col-span-12 md:col-span-4">
        <BaseInput
          v-model="agencia"
          label="Agência"
          placeholder="0000"
          :error="submitCount > 0 ? errors.agencia : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-4">
        <BaseInput
          v-model="conta"
          label="Conta"
          placeholder="00000-0"
          :error="submitCount > 0 ? errors.conta : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-4">
        <BaseInput
          v-model="pix"
          label="Chave PIX"
          placeholder="CPF, CNPJ, email ou telefone"
          :error="submitCount > 0 ? errors.pix : ''"
          :disabled="disabled"
        />
      </div>

    </div>
  </section>
</template>