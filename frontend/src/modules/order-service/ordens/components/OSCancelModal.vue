<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import ConfirmationTemplate from '@/shared/components/templates/ConfirmationTemplate.vue';
import { AlertTriangle } from 'lucide-vue-next';
import { useOSCancel } from '../composables/useOSCancel';
import type { OrdemServicoListRead } from '../types/ordemServico.types';

interface Props {
  isOpen: boolean;
  os: OrdemServicoListRead | null;
  isLoading?: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  close: [];
  confirm: [payload: { motivo: string; print: boolean }];
}>();

const { motivo, shouldPrint, error, validate, reset } = useOSCancel();

function handleClose() {
  reset();
  emit('close');
}

function handleConfirm() {
  if (!validate()) return;
  emit('confirm', { motivo: motivo.value, print: shouldPrint.value });
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Cancelar O.S.?"
    size="sm"
    @close="handleClose"
  >
    <ConfirmationTemplate
      :icon="AlertTriangle"
      icon-bg-class="bg-brand-primary-light"
      icon-color-class="text-brand-primary"
    >
      <template #description>
        <p class="text-sm text-slate-500 leading-relaxed">
          Tem certeza que deseja cancelar a Ordem de Serviço
          <span class="font-bold text-slate-800 block mt-1 text-base">
            {{ os?.numero ? `Nº ${os.numero}` : 'Selecionada' }}
          </span>
        </p>
      </template>

      <div class="space-y-4">
        <BaseTextarea
          v-model="motivo"
          label="Motivo do Cancelamento"
          placeholder="Informe o motivo..."
          :rows="3"
          :error="error"
        />

        <div class="flex justify-center">
          <BaseCheckbox
            v-model="shouldPrint"
            label="Imprimir Comprovante"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex gap-3 w-full">
          <BaseButton
            variant="secondary"
            class="flex-1"
            @click="handleClose"
          >
            VOLTAR
          </BaseButton>
          <BaseButton
            variant="primary"
            :is-loading="isLoading"
            class="flex-1"
            @click="handleConfirm"
          >
            CONFIRMAR
          </BaseButton>
        </div>
      </template>
    </ConfirmationTemplate>
  </BaseModal>
</template>
