<script setup lang="ts">
import { CirclePlus, CircleMinus } from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    disabled?: boolean;
  }>(),
  {
    disabled: false,
  },
);

const emit = defineEmits<{
  (e: 'increase'): void;
  (e: 'decrease'): void;
}>();

const quantity = defineModel({
  type: Number,
  default: 1,
});

function decrease() {
  if (props.disabled) return;
  if (quantity.value <= 1) return;

  emit('decrease');
}

function increase() {
  if (props.disabled) return;

  emit('increase');
}
</script>

<template>
  <div class="w-full h-full flex border-2 border-zinc-200 rounded-lg overflow-hidden">
    <button
      class="flex items-center justify-center w-1/4 bg-zinc-50 hover:bg-zinc-200 disabled:hover:bg-zinc-50 transition-colors cursor-pointer disabled:cursor-not-allowed"
      type="button"
      :disabled="disabled"
      @click="decrease"
    >
      <CircleMinus :size="15" />
    </button>
    <input
      type="text"
      inputmode="numeric"
      v-model="quantity"
      class="input-number-no-spinner flex-1 w-full border-x-2 border-zinc-200 focus:outline-none text-center font-poppins text-sm disabled:cursor-not-allowed"
      maxlength="4"
      :disabled="disabled"
    />
    <button
      class="flex items-center justify-center w-1/4 bg-zinc-50 hover:bg-zinc-200 disabled:hover:bg-zinc-50 transition-colors cursor-pointer disabled:cursor-not-allowed"
      type="button"
      :disabled="disabled"
      @click="increase"
    >
      <CirclePlus :size="15" />
    </button>
  </div>
</template>
