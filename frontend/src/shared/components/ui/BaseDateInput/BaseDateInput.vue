<script setup lang="ts">
/**
 * @component BaseDateInput
 * @description Input de data com máscara DD/MM/AAAA, conversão ISO (YYYY-MM-DD)
 * e ícone de calendário com date picker nativo como fallback.
 */

import { ref, watch, computed } from 'vue';
import { Calendar } from 'lucide-vue-next';

interface Props {
  label?: string;
  placeholder?: string;
  required?: boolean;
  error?: string;
  disabled?: boolean;
  id?: string;
  inputClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'DD/MM/AAAA',
  required: false,
});

const model = defineModel<string>();

const displayValue = ref('');
const nativePicker = ref<HTMLInputElement | null>(null);
const isInternalUpdate = ref(false);
const uniqueId = props.id || `date-${Math.random().toString(36).slice(2, 7)}`;

// --- Conversão de formatos ---

function isoToDisplay(iso: string): string {
  if (!iso || iso.length < 10) return '';
  const [y, m, d] = iso.split('-');
  if (!y || !m || !d) return '';
  return `${d}/${m}/${y}`;
}

function displayToIso(display: string): string {
  if (!display || display.length !== 10) return '';
  const [d, m, y] = display.split('/');
  const day = parseInt(d, 10);
  const month = parseInt(m, 10);
  const year = parseInt(y, 10);
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1900 || year > 2100) return '';
  return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;
}

// --- Sync model -> display (populate externo) ---

watch(
  () => model.value,
  (newVal) => {
    if (isInternalUpdate.value) {
      isInternalUpdate.value = false;
      return;
    }
    displayValue.value = isoToDisplay(newVal || '');
  },
  { immediate: true },
);

// --- Evento maska ---

function onMaskaUpdate(event: CustomEvent) {
  const masked = event.detail?.masked ?? displayValue.value;
  displayValue.value = masked;

  if (masked.length === 10) {
    const iso = displayToIso(masked);
    if (iso) {
      isInternalUpdate.value = true;
      model.value = iso;
    }
  } else if (masked.length === 0) {
    isInternalUpdate.value = true;
    model.value = '';
  }
}

// --- Calendário nativo ---

function openNativePicker() {
  nativePicker.value?.showPicker?.();
}

function onNativeChange(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.value) {
    isInternalUpdate.value = false;
    model.value = input.value;
  }
}

// --- Styling ---

const inputClasses = computed(() => {
  if (props.inputClass) {
    return ['w-full text-sm pr-9', props.inputClass];
  }
  return [
    'w-full px-3 py-2 border rounded-md transition-colors duration-200 outline-none text-sm',
    'placeholder:text-gray-400 text-gray-700',
    props.error
      ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
      : 'border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary',
    props.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white',
    'pr-9',
  ];
});
</script>

<template>
  <div class="w-full">
    <label
      v-if="label"
      :for="uniqueId"
      class="block select-none text-xs font-medium text-gray-700 mb-1"
    >
      {{ label }}
      <span v-if="required" class="text-red-600"> * </span>
    </label>

    <div class="relative">
      <input
        v-maska
        data-maska="##/##/####"
        :id="uniqueId"
        type="text"
        :value="displayValue"
        :placeholder="placeholder"
        :required="required"
        :disabled="disabled"
        :class="inputClasses"
        @maska="onMaskaUpdate"
      />

      <!-- Ícone de calendário + picker nativo oculto -->
      <div class="absolute right-2 top-1/2 -translate-y-1/2">
        <button
          type="button"
          class="text-gray-400 hover:text-gray-600 focus:outline-none cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="disabled"
          tabindex="-1"
          @click="openNativePicker"
        >
          <Calendar :size="16" />
        </button>
        <input
          ref="nativePicker"
          type="date"
          class="absolute inset-0 opacity-0 w-full h-full cursor-pointer"
          :disabled="disabled"
          :value="model"
          tabindex="-1"
          @change="onNativeChange"
        />
      </div>
    </div>

    <p v-if="error" class="select-none mt-0.5 text-xs text-red-500">
      {{ error }}
    </p>
  </div>
</template>
