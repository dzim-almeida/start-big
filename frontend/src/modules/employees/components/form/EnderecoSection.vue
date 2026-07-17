<script setup lang="ts">
/**
 * @component EnderecoSection
 * @description Form section for employee addresses (dynamic list)
 */

import AddressSection from '@/shared/components/form/AddressSection.vue';
import { useEmployeeForm } from '../../composables/useEmployeeForm';


interface Props {
  submitCount: number;
  disabled?: boolean;
}

const props = defineProps<Props>();

const { enderecos, handleAddEndereco, handleRemoveEndereco, errors } = useEmployeeForm()
</script>

<template>
  <AddressSection
    v-model="enderecos"
    :onAdd="handleAddEndereco"
    :onRemove="handleRemoveEndereco"
    :submit-count="props.submitCount"
    :errors="errors"
    :disabled="props.disabled"
  />
</template>
