<script setup lang="ts">
/**
 * @component ContactSection
 * @description Seção de contato compartilhada (email, telefone, celular)
 * Reutilizável em múltiplos módulos (enterprise, employees, customers)
 */

import BaseInput from '../ui/BaseInput/BaseInput.vue';

interface Props {
  email?: string;
  telefone?: string;
  celular?: string;
  emailLabel?: string;
  telefoneLabel?: string;
  celularLabel?: string;
  disabled?: boolean;
  emailError?: string;
  telefoneError?: string;
  celularError?: string;
  showTitle?: boolean;
  title?: string;
}

const props = withDefaults(defineProps<Props>(), {
  email: '',
  telefone: '',
  celular: '',
  emailLabel: 'E-mail',
  telefoneLabel: 'Telefone',
  celularLabel: 'Celular',
  disabled: false,
  emailError: '',
  telefoneError: '',
  celularError: '',
  showTitle: true,
  title: 'Contato',
});

const emit = defineEmits<{
  'update:email': [value: string];
  'update:telefone': [value: string];
  'update:celular': [value: string];
}>();
</script>

<template>
  <section class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
    <h3
      v-if="showTitle"
      class="text-base font-bold text-gray-800 mb-6 pb-3 border-b border-gray-100"
    >
      {{ title }}
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="md:col-span-2">
        <BaseInput
          :model-value="email"
          :label="emailLabel"
          type="email"
          placeholder="exemplo@email.com"
          :disabled="disabled"
          :error="emailError"
          @update:model-value="emit('update:email', $event as string)"
        />
      </div>

      <BaseInput
        :model-value="telefone"
        :label="telefoneLabel"
        mask="(##) ####-####"
        placeholder="(00) 0000-0000"
        :disabled="disabled"
        :error="telefoneError"
        @update:model-value="emit('update:telefone', $event as string)"
      />

      <BaseInput
        :model-value="celular"
        :label="celularLabel"
        mask="(##) #####-####"
        placeholder="(00) 00000-0000"
        :disabled="disabled"
        :error="celularError"
        @update:model-value="emit('update:celular', $event as string)"
      />
    </div>
  </section>
</template>
