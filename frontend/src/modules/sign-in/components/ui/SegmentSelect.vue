<script setup lang="ts">
/**
 * @component SegmentSelect
 * @description Select customizado para segmentos com ícones.
 * Replica o visual do BaseSelect mas inclui ícones ao lado de cada opção.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { ChevronDown } from 'lucide-vue-next';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';

import type { SegmentOption } from '../../types/sign-in.types';

interface Props {
  options: SegmentOption[];
  label?: string;
  required?: boolean;
  error?: string;
  disabled?: boolean;
  placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
  disabled: false,
  placeholder: 'Selecione o segmento',
});

const model = defineModel<string>();

const isOpen = ref(false);
const selectRef = ref<HTMLDivElement | null>(null);
const searchQuery = ref('');

const selectedOption = computed(() =>
  props.options.find((opt) => opt.id === model.value),
);

const filteredOptions = computed(() => {
  if (!searchQuery.value.trim()) return props.options;
  const query = searchQuery.value.toLowerCase();
  return props.options.filter((opt) => opt.label.toLowerCase().includes(query));
});

const displayValue = computed(() => {
  if (isOpen.value) return searchQuery.value;
  return selectedOption.value?.label || '';
});

function openDropdown(): void {
  if (props.disabled) return;
  isOpen.value = true;
  searchQuery.value = '';
}

function closeDropdown(): void {
  isOpen.value = false;
  searchQuery.value = '';
}

function selectOption(option: SegmentOption): void {
  model.value = option.id;
  closeDropdown();
}

function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement;
  searchQuery.value = target.value;
  if (!isOpen.value) isOpen.value = true;
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault();
    closeDropdown();
  }
}

onClickOutside(selectRef, () => {
  if (isOpen.value) closeDropdown();
});
</script>

<template>
  <div ref="selectRef" class="w-full">
    <label v-if="label" class="block select-none text-xs font-medium text-gray-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-600"> * </span>
    </label>

    <div class="relative">
      <!-- Input com ícone do segmento selecionado -->
      <div class="relative flex items-center">
        <div
          v-if="selectedOption && !isOpen"
          class="absolute left-2.5 flex items-center text-brand-primary"
        >
          <SegmentIcons :icon="selectedOption.icon" :size="16" />
        </div>
        <input
          :value="displayValue"
          :placeholder="placeholder"
          :disabled="disabled"
          :required="required"
          autocomplete="off"
          class="w-full py-2 pr-8 border rounded-md transition-colors duration-200 outline-none text-sm cursor-pointer placeholder:text-gray-400 text-gray-700"
          :class="[
            selectedOption && !isOpen ? 'pl-9' : 'pl-3',
            error
              ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
              : 'border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary',
            disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white',
          ]"
          @input="handleInput"
          @focus="openDropdown"
          @keydown="handleKeydown"
        />
        <div class="absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
          <LucideIcon :icon="ChevronDown" />
        </div>
      </div>

      <!-- Dropdown -->
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
          class="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          <ul v-if="filteredOptions.length > 0" class="py-1">
            <li
              v-for="option in filteredOptions"
              :key="option.id"
              class="flex items-center gap-2.5 px-3 py-2 text-sm cursor-pointer transition-colors"
              :class="
                model === option.id
                  ? 'bg-brand-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              "
              @click="selectOption(option)"
            >
              <SegmentIcons
                :icon="option.icon"
                :size="16"
                class="shrink-0"
              />
              <span>{{ option.label }}</span>
            </li>
          </ul>
          <div
            v-else
            class="flex justify-center items-center px-3 py-2 text-sm text-gray-500"
          >
            Nenhuma opção encontrada
          </div>
        </div>
      </Transition>
    </div>

    <p v-if="error" class="select-none mt-0.5 text-xs text-red-500">
      {{ error }}
    </p>
  </div>
</template>
