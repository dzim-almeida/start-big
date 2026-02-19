<script setup lang="ts">
interface Props {
  label?: string;
  placeholder?: string;
  rows?: number;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

withDefaults(defineProps<Props>(), {
  rows: 3,
  required: false,
});

const model = defineModel<string>();
</script>

<template>
  <div>
    <label v-if="label" class="block text-sm font-medium text-zinc-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <textarea
      v-model="model"
      :placeholder="placeholder"
      :rows="rows"
      :disabled="disabled"
      :class="[
        'w-full px-3 py-2 border rounded-lg transition-colors duration-200 outline-none text-sm placeholder:text-gray-400 text-gray-700 resize-none',
        error
          ? 'border-red-300 focus:border-red-500 focus:ring-1 focus:ring-red-500'
          : 'border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary',
        disabled ? 'bg-gray-50 cursor-not-allowed opacity-60' : 'bg-white',
      ]"
    />
    <p v-if="error" class="mt-1 text-xs text-red-500">{{ error }}</p>
  </div>
</template>
