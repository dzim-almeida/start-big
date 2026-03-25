
// ============================================================================
// COMPONENTE: DadosEntregadorSection (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Formulário de dados pessoais e veiculares do entregador.
// FUNCIONALIDADES: Máscara de CPF em tempo real, validação baseada em tentativas 
//                  de envio (submitCount) e campos específicos de telemetria básica (placa/veículo).
// ============================================================================
<script setup lang="ts">
import { Bike } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { useFornecedorForm } from '../../composables/useFornecedorForm';

interface Props {
  submitCount: number;
  disabled?: boolean;
}

defineProps<Props>();

const {
  nome,
  cpf,
  telefone,
  celular,
  email,
  veiculo,
  placa,
  errors,
} = useFornecedorForm();

function handleCpfInput(value: string) {
  const digits = value.replace(/\D/g, '').slice(0, 11);
  cpf.value = digits
    .replace(/^(\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1-$2');
}
</script>

<template>
  <section>
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-brand-primary"
      >
        <LucideIcon :icon="Bike" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Dados do Entregador</h3>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <div class="col-span-12 md:col-span-7">
        <BaseInput
          v-model="nome"
          label="Nome Completo"
          placeholder="Nome do entregador"
          :required="true"
          :error="submitCount > 0 ? errors.nome : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-5">
        <BaseInput
          :model-value="cpf"
          label="CPF"
          placeholder="000.000.000-00"
          :required="true"
          :error="submitCount > 0 ? errors.cpf : ''"
          :disabled="disabled"
          @update:model-value="handleCpfInput($event as string)"
        />
      </div>

      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="telefone"
          label="Telefone"
          placeholder="(00) 0000-0000"
          mask="(##) ####-####"
          :error="submitCount > 0 ? errors.telefone : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="celular"
          label="Celular"
          placeholder="(00) 00000-0000"
          mask="(##) #####-####"
          :error="submitCount > 0 ? errors.celular : ''"
          :disabled="disabled"
        />
      </div>

      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="email"
          label="Email"
          type="email"
          placeholder="entregador@email.com"
          :error="submitCount > 0 ? errors.email : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="veiculo"
          label="Veículo"
          placeholder="Ex: Moto Honda CG 160"
          :error="submitCount > 0 ? errors.veiculo : ''"
          :disabled="disabled"
        />
      </div>

      <div class="col-span-12 md:col-span-5">
        <BaseInput
          v-model="placa"
          label="Placa do Veículo"
          placeholder="Ex: ABC-1234"
          :error="submitCount > 0 ? errors.placa : ''"
          :disabled="disabled"
        />
      </div>
    </div>
  </section>
</template>
