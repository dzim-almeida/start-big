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
  inputClass?: string;
  variant?: 'default' | 'success' | 'warning' | 'info';
}

// 2. Use withDefaults com uma função para a propriedade 'options'
const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  options: () => ({
    currency: 'BRL',
    locale: 'pt-BR',
    autoDecimalDigits: true,
    currencyDisplay: 'symbol' as CurrencyDisplay,
    hideCurrencySymbolOnFocus: false,
  })
});

defineEmits<{
  blur: [];
  enter: [];
  keydown: [event: KeyboardEvent];
}>();

const uniqueId = props.id || `input-${Math.random().toString(36).slice(2, 7)}`;

const model = defineModel<number>();

// 3. Inicialize o hook usando as props.options
const { inputRef, setValue } = useCurrencyInput(props.options);

const inputClasses = computed(() => {
  let stateClasses = 'border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary';
  let bgClass = props.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white';
  let textClass = 'text-gray-700';

  if (props.error) {
    stateClasses = 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500';
    textClass = 'text-red-700';
  } else if (props.variant === 'success') {
    stateClasses = 'border-emerald-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500';
    bgClass = props.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-emerald-50/50';
    textClass = 'text-emerald-700 font-bold';
  } else if (props.variant === 'warning') {
    stateClasses = 'border-amber-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500';
    bgClass = props.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-amber-50/50';
    textClass = 'text-amber-700 font-bold';
  } else if (props.variant === 'info') {
    stateClasses = 'border-blue-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500';
    bgClass = props.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-blue-50/50';
    textClass = 'text-blue-700 font-bold';
  }

  return [
    'w-full px-3 py-2 border rounded-md transition-all duration-200 outline-none text-sm placeholder:text-gray-400',
    stateClasses,
    bgClass,
    textClass,
    props.inputClass,
  ];
});

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

defineExpose({
  inputRef,
});
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
      @blur="$emit('blur')"
      @keydown.enter="$emit('enter')"
      @keydown="$emit('keydown', $event)"
    />

    <p v-if="error" class="mt-0.5 text-xs text-red-500">
      {{ error }}
    </p>
  </div>
</template>