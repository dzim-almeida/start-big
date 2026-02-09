<script setup lang="ts">
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { useServicoForm } from '../../../composables/useServicoForm';

defineProps<{
  disabled?: boolean;
}>();

const { descricao, valor, errors } = useServicoForm();
</script>

<template>
  <section class="space-y-4">
    <BaseInput
      v-model="descricao"
      label="Descrição do serviço"
      placeholder="Ex: Troca de display"
      :error="errors.descricao"
      :disabled="disabled"
      required
    />

    <MoneyInput
      v-model="valor"
      label="Valor base"
      :error="errors.valor"
      :disabled="disabled"
      required
    />
  </section>
</template>
