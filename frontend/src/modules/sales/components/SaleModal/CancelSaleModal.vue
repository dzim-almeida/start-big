<script setup lang="ts">
import { ref, computed } from 'vue';
import { AlertTriangle } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useCancelSaleMutation } from '../../composables/mutates/useCancelSaleMutation';
import { useGerenteAprovacao } from '@/shared/composables/useGerenteAprovacao';
import { useToast } from '@/shared/composables/useToast';
import GerenteAprovacaoModal from '@/shared/components/commons/GerenteAprovacaoModal/GerenteAprovacaoModal.vue';
import type { SaleRead } from '../../schemas/sale.schema';

const MIN_MOTIVO = 10;

const props = defineProps<{
  isOpen: boolean;
  sale: SaleRead | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'success'): void;
}>();

const motivo = ref('');
const touched = ref(false);
const cancelMutation = useCancelSaleMutation();
const gerente = useGerenteAprovacao();
const toast = useToast();

const motivoTrimmed = computed(() => motivo.value.trim());
const isValid = computed(() => motivoTrimmed.value.length >= MIN_MOTIVO);
const showError = computed(() => touched.value && !isValid.value);
const errorMessage = computed(() => {
  if (motivoTrimmed.value.length === 0) return 'O motivo é obrigatório.';
  return `Mínimo de ${MIN_MOTIVO} caracteres (${motivoTrimmed.value.length}/${MIN_MOTIVO}).`;
});

async function executarCancelamento(codigoGerente?: string) {
  if (!props.sale) return;
  try {
    gerente.isLoading.value = true;
    await cancelMutation.mutateAsync(
      { saleId: props.sale.id, motivo: motivoTrimmed.value, codigoGerente },
    );
    motivo.value = '';
    touched.value = false;
    emit('success');
  } catch (error: any) {
    const detail = error?.response?.data?.detail;
    if (detail === 'REQUER_APROVACAO_GERENTE') {
      const pin = await gerente.pedirPin();
      if (pin) await executarCancelamento(pin);
    } else if (detail === 'PIN_GERENTE_INVALIDO') {
      toast.error('PIN do gerente inválido');
      const pin = await gerente.pedirPin();
      if (pin) await executarCancelamento(pin);
    }
  } finally {
    gerente.isLoading.value = false;
  }
}

function handleConfirm() {
  touched.value = true;
  if (!isValid.value) return;
  executarCancelamento();
}

function handleClose() {
  motivo.value = '';
  touched.value = false;
  emit('close');
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Cancelar Venda?"
    size="sm"
    overlay
    @close="handleClose"
  >
    <div class="flex flex-col items-center gap-4 py-2">
      <div class="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center">
        <AlertTriangle :size="28" class="text-red-500" />
      </div>

      <p class="text-sm text-slate-500 text-center leading-relaxed">
        Cancelar a
        <span class="font-bold text-slate-800">
          Venda #{{ String(sale?.numero_venda).padStart(6, '0') }}
        </span>
        irá estornar o estoque de todos os produtos.
        <span class="block mt-1 text-red-500 font-medium">Esta ação não pode ser desfeita.</span>
      </p>

      <div class="w-full">
        <label class="block text-xs font-semibold text-zinc-600 mb-1.5">
          Motivo do cancelamento <span class="text-red-500">*</span>
        </label>
        <textarea
          v-model="motivo"
          placeholder="Descreva o motivo do cancelamento (mínimo 10 caracteres)..."
          rows="3"
          maxlength="500"
          :class="[
            'w-full px-3 py-2 border rounded-lg text-sm placeholder:text-gray-400 text-gray-700 resize-none outline-none transition-colors',
            showError
              ? 'border-red-400 focus:border-red-500 focus:ring-1 focus:ring-red-500'
              : 'border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary',
          ]"
          @blur="touched = true"
        />
        <div class="flex justify-between items-center mt-1">
          <p v-if="showError" class="text-[11px] text-red-500">{{ errorMessage }}</p>
          <span v-else class="text-[10px] text-zinc-400" />
          <span class="text-[10px] text-zinc-400 ml-auto">{{ motivoTrimmed.length }}/500</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex gap-3 w-full">
        <BaseButton
          variant="secondary"
          class="flex-1"
          :disabled="cancelMutation.isPending.value"
          @click="handleClose"
        >
          VOLTAR
        </BaseButton>
        <BaseButton
          variant="danger"
          class="flex-1"
          :is-loading="cancelMutation.isPending.value"
          @click="handleConfirm"
        >
          CANCELAR VENDA
        </BaseButton>
      </div>
    </template>
  </BaseModal>

  <GerenteAprovacaoModal
    :is-open="gerente.isOpen.value"
    :is-loading="gerente.isLoading.value"
    @confirmar="gerente.confirmar"
    @cancelar="gerente.cancelar"
  />
</template>
