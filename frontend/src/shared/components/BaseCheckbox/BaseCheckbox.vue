<script setup lang="ts">
/**
 * @component BaseCheckbox
 * @description Componente de checkbox reutilizável com suporte a v-model,
 * labels e estados de erro.
 */

interface CheckboxProps {
  label?: string;
  disabled?: boolean;
  id?: string;
}

const props = defineProps<CheckboxProps>();

const value = defineModel<boolean>();
</script>

<template>
  <div class="flex items-center gap-1.5">
    <input
      v-model="value"
      :id="id || label"
      type="checkbox"
      :disabled="disabled"
      class="w-3.5 h-3.5 border-gray-300 rounded text-brand-primary focus:ring-brand-primary focus:ring-1 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
    />
    <label
      v-if="label"
      :for="id || label"
      class="text-xs text-gray-600 cursor-pointer select-none"
      :class="{ 'opacity-50 cursor-not-allowed': disabled }"
    >
      {{ label }}
    </label>
  </div>
</template>
