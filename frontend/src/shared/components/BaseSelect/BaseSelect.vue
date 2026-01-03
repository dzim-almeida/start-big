<script setup lang="ts">
/**
 * @component BaseSelect
 * @description Componente de select com autocomplete/filtro.
 * Permite buscar e filtrar opções conforme o usuário digita.
 */

import Icons from '@/modules/onboarding/components/icons/Icons.vue';
import { computed, ref, watch, onMounted, onUnmounted } from 'vue';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  options: SelectOption[];
  label?: string;
  placeholder?: string;
  required?: boolean;
  error?: string;
  disabled?: boolean;
  id?: string;
  emptyMessage?: string;
}

const props = withDefaults(defineProps<SelectProps>(), {
  required: false,
  disabled: false,
  emptyMessage: 'Nenhuma opção encontrada',
});

const model = defineModel<string>();

const searchQuery = ref('');
const isOpen = ref(false);
const selectRef = ref<HTMLDivElement>();
const inputRef = ref<HTMLInputElement>();
const highlightedIndex = ref(-1);

const uniqueId = props.id || `select-${Math.random().toString(36).slice(2, 7)}`;

const filteredOptions = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.options;
  }

  const query = searchQuery.value.toLowerCase();
  return props.options.filter(
    (option) =>
      option.label.toLowerCase().includes(query) ||
      option.value.toLowerCase().includes(query)
  );
});

const selectedOption = computed(() => {
  return props.options.find((opt) => opt.value === model.value);
});

const displayValue = computed(() => {
  if (isOpen.value) {
    return searchQuery.value;
  }
  return selectedOption.value?.label || '';
});

const inputClasses = computed(() => [
  'w-full px-3 py-2 pr-8 border rounded-md transition-colors duration-200 outline-none text-sm cursor-pointer',
  'placeholder:text-gray-400 text-gray-700',
  props.error
    ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
    : 'border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary',
  props.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white',
]);

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement;
  searchQuery.value = target.value;
  if (!isOpen.value) {
    isOpen.value = true;
  }
}

function openDropdown() {
  if (props.disabled) return;
  isOpen.value = true;
  searchQuery.value = '';
  highlightedIndex.value = -1;
  setTimeout(() => inputRef.value?.focus(), 0);
}

function closeDropdown() {
  isOpen.value = false;
  searchQuery.value = '';
  highlightedIndex.value = -1;
}

function selectOption(option: SelectOption) {
  model.value = option.value;
  closeDropdown();
}

function handleKeydown(event: KeyboardEvent) {
  if (!isOpen.value) {
    if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowDown') {
      event.preventDefault();
      openDropdown();
    }
    return;
  }

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault();
      if (highlightedIndex.value < filteredOptions.value.length - 1) {
        highlightedIndex.value++;
        scrollToHighlighted();
      }
      break;

    case 'ArrowUp':
      event.preventDefault();
      if (highlightedIndex.value > 0) {
        highlightedIndex.value--;
        scrollToHighlighted();
      }
      break;

    case 'Enter':
      event.preventDefault();
      if (highlightedIndex.value >= 0 && filteredOptions.value[highlightedIndex.value]) {
        selectOption(filteredOptions.value[highlightedIndex.value]);
      }
      break;

    case 'Escape':
      event.preventDefault();
      closeDropdown();
      break;
  }
}

function scrollToHighlighted() {
  setTimeout(() => {
    const optionElement = document.querySelector(`[data-option-index="${highlightedIndex.value}"]`);
    optionElement?.scrollIntoView({ block: 'nearest' });
  }, 0);
}

function handleClickOutside(event: MouseEvent) {
  if (selectRef.value && !selectRef.value.contains(event.target as Node)) {
    closeDropdown();
  }
}

watch(
  () => filteredOptions.value,
  () => {
    if (highlightedIndex.value >= filteredOptions.value.length) {
      highlightedIndex.value = filteredOptions.value.length - 1;
    }
  }
);

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <div ref="selectRef" class="w-full">
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
        ref="inputRef"
        :id="uniqueId"
        :value="displayValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :class="inputClasses"
        autocomplete="off"
        @input="handleInput"
        @focus="openDropdown"
        @keydown="handleKeydown"
      />

      <div
        class="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400"
      >
        <Icons icon="select" />
      </div>

      <Transition
        enter-active-class="transition ease-out duration-100"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition ease-in duration-75"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="isOpen"
          class="absolute z-50 w-full h-40 mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          <ul v-if="filteredOptions.length > 0" class="py-1">
            <li
              v-for="(option, index) in filteredOptions"
              :key="option.value"
              :data-option-index="index"
              class="px-3 py-2 text-sm cursor-pointer transition-colors"
              :class="[
                highlightedIndex === index || model === option.value
                  ? 'bg-brand-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100',
              ]"
              @click="selectOption(option)"
              @mouseenter="highlightedIndex = index"
            >
              {{ option.label }}
            </li>
          </ul>
          <div v-else class="flex justify-center items-center h-full px-3 py-2 text-sm text-gray-500 text-center">
            {{ emptyMessage }}
          </div>
        </div>
      </Transition>
    </div>

    <p v-if="error" class="select-none mt-0.5 text-xs text-red-500">
      {{ error }}
    </p>
  </div>
</template>
