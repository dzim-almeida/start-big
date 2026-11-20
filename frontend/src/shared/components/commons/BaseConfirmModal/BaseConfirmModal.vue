<script setup lang="ts">
import { computed } from 'vue';
import { AlertTriangle, Info, AlertCircle } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import type { DescricaoConfirmacao, TrechoDescricao } from '@/shared/types/confirmacao.types';

interface Props {
  isOpen: boolean;
  title: string;
  // Texto puro ou lista de trechos com negrito; nunca HTML (LIC-04, D-17)
  description?: DescricaoConfirmacao;
  confirmLabel?: string;
  confirmText?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  isDanger?: boolean;
  isLoading?: boolean;
  icon?: any;
  overlay?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  confirmLabel: 'Confirmar',
  cancelLabel: 'Cancelar',
  variant: 'info',
  isDanger: false,
  isLoading: false,
  overlay: false,
});

const emit = defineEmits<{
  close: [];
  confirm: [];
}>();

const effectiveVariant = computed(() => {
  if (props.isDanger) return 'danger';
  return props.variant;
});

// A descrição sempre vira uma lista de trechos, para o template ter um caminho só.
const trechos = computed<TrechoDescricao[]>(() =>
  Array.isArray(props.description) ? props.description : [props.description],
);

const effectiveConfirmLabel = computed(() => props.confirmText || props.confirmLabel);

const bannerClasses = computed(() => {
  switch (effectiveVariant.value) {
    case 'danger': return 'bg-red-50 border-red-100 text-red-700';
    case 'warning': return 'bg-amber-50 border-amber-100 text-amber-700';
    default: return 'bg-blue-50 border-blue-100 text-blue-700';
  }
});

const iconClass = computed(() => {
  switch (effectiveVariant.value) {
    case 'danger': return 'text-red-500';
    case 'warning': return 'text-amber-500';
    default: return 'text-blue-500';
  }
});

const confirmButtonClass = computed(() => {
  switch (effectiveVariant.value) {
    case 'danger': return 'bg-red-500 hover:bg-red-600 border-red-500 text-white';
    case 'warning': return 'bg-amber-500 hover:bg-amber-600 border-amber-500 text-white';
    default: return '';
  }
});

const defaultIcon = computed(() => {
  switch (effectiveVariant.value) {
    case 'danger': return AlertTriangle;
    case 'warning': return AlertCircle;
    default: return Info;
  }
});
</script>

<template>
  <BaseModal :is-open="isOpen" :title="title" size="sm" :overlay="overlay" @close="emit('close')">
    <div :class="['flex items-start gap-3 p-3 border rounded-xl', bannerClasses]">
      <component
        :is="icon || defaultIcon"
        :size="18"
        :class="['shrink-0 mt-0.5', iconClass]"
      />
      <div class="text-sm leading-snug">
        <!-- Quem precisa de um destaque mais elaborado usa o slot "description". -->
        <slot name="description">
          <!-- Cada trecho é mostrado com {{ }}: o Vue escapa o texto, então nada
               do que o usuário digitou vira HTML (LIC-04, D-17). -->
          <span>
            <template v-for="(trecho, indice) in trechos" :key="indice">
              <strong v-if="typeof trecho === 'object'">{{ trecho.negrito }}</strong>
              <template v-else>{{ trecho }}</template>
            </template>
          </span>
        </slot>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <BaseButton variant="secondary" class="px-5" @click="emit('close')">
          {{ cancelLabel }}
        </BaseButton>
        <BaseButton
          variant="primary"
          class="px-5"
          :class="confirmButtonClass"
          :is-loading="isLoading"
          @click="emit('confirm')"
        >
          {{ effectiveConfirmLabel }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
