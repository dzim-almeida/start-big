// ============================================================================
// COMPONENTE: DadosTransportadoraSection (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Formulário de dados para empresas de logística e frete.
// FUNCIONALIDADES: Coleta de dados fiscais (CNPJ/IE) e contato operacional, 
//                  utilizando ícone de Truck para diferenciação visual rápida.
// ============================================================================
<script setup lang="ts">
import { Truck } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { useFornecedorForm } from '../../composables/useFornecedorForm';

interface Props {
  submitCount: number;
  disabled?: boolean;
}

defineProps<Props>();

const {
  cnpj,
  nome,
  nome_fantasia,
  ie,
  telefone,
  celular,
  email,
  representante,
  errors,
} = useFornecedorForm();

function handleCnpjInput(value: string) {
  const digits = value.replace(/\D/g, '').slice(0, 14);
  cnpj.value = digits
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2');
}
</script>

<template>
  <section>
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-brand-primary"
      >
        <LucideIcon :icon="Truck" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Dados da Transportadora</h3>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <div class="col-span-12 md:col-span-7">
        <BaseInput
          v-model="nome"
          label="Razão Social"
          placeholder="Nome oficial da transportadora"
          :required="true"
          :error="submitCount > 0 ? errors.nome : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-5">
        <BaseInput
          :model-value="cnpj"
          label="CNPJ"
          placeholder="00.000.000/0000-00"
          :required="true"
          :error="submitCount > 0 ? errors.cnpj : ''"
          :disabled="disabled"
          @update:model-value="handleCnpjInput($event as string)"
        />
      </div>

      <div class="col-span-12 md:col-span-7">
        <BaseInput
          v-model="nome_fantasia"
          label="Nome Fantasia"
          placeholder="Nome comercial (opcional)"
          :error="submitCount > 0 ? errors.nome_fantasia : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-5">
        <BaseInput
          v-model="ie"
          label="Inscrição Estadual"
          placeholder="IE (opcional)"
          :error="submitCount > 0 ? errors.ie : ''"
          :disabled="disabled"
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
          placeholder="contato@transportadora.com"
          :error="submitCount > 0 ? errors.email : ''"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-12 md:col-span-6">
        <BaseInput
          v-model="representante"
          label="Contato Operacional"
          placeholder="Nome do responsável operacional"
          :error="submitCount > 0 ? errors.representante : ''"
          :disabled="disabled"
        />
      </div>
    </div>
  </section>
</template>
