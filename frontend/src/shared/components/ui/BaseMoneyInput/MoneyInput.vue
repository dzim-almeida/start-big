<script setup lang="ts">
import { computed, watch } from 'vue';
import { 
  useCurrencyInput, 
  type CurrencyInputOptions, 
  CurrencyDisplay
} from 'vue-currency-input';

interface Props {
  label?: string;
  required?: boolean;
  error?: string;
  disabled?: boolean;
  id?: string;
  options?: CurrencyInputOptions; // Adicionado para flexibilidade
}

// 2. Use withDefaults com uma função para a propriedade 'options'
const props = withDefaults(defineProps<Props>(), {
  options: () => ({
    currency: 'BRL',
    locale: 'pt-BR',
    autoDecimalDigits: true,
    currencyDisplay: 'symbol' as CurrencyDisplay,
    hideCurrencySymbolOnFocus: false,
  })
});

const uniqueId = props.id || `input-${Math.random().toString(36).slice(2, 7)}`;

const model = defineModel<number>();

// 3. Inicialize o hook usando as props.options
const { inputRef, setValue } = useCurrencyInput(props.options);

const inputClasses = computed(() => [
  'w-full px-3 py-2 border rounded-md transition-colors duration-200 outline-none text-sm',
  'placeholder:text-gray-400 text-gray-700',
  props.error
    ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
    : 'border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary',
  props.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white',
]);

watch(
  () => model.value,
  (value) => {
    if (value === null || value === undefined) {
      setValue(0);
    } else {
      setValue(value as number);
    }
  },
);
</script>

<template>
  <div class="w-full">
    <label v-if="label" :for="uniqueId" class="block text-xs font-medium text-gray-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-600"> * </span>
    </label>

    <input
      ref="inputRef"
      type="text"
      :id="uniqueId"
      :required="required"
      :disabled="disabled"
      :class="inputClasses"
    />

    <p v-if="error" class="mt-0.5 text-xs text-red-500">
      {{ error }}
    </p>
  </div>
</template>