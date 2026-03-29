<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import ConfirmationTemplate from '@/shared/components/templates/ConfirmationTemplate.vue';
import { AlertTriangle } from 'lucide-vue-next';
import { useOSCancelarForm } from '../composables/form/useOSCancelar.form';

interface Props {
  isOpen: boolean;
  osNumero: string | null;
  osDisplayNumber?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  cancelled: [payload: { shouldPrint: boolean }];
}>();

const shouldPrint = ref(false);

const osNumberRef = computed(() => props.osNumero);

const cancelarForm = useOSCancelarForm({
  osNumber: osNumberRef,
  onSuccess: () => {
    emit('cancelled', { shouldPrint: shouldPrint.value });
    shouldPrint.value = false;
  },
});

watch(() => props.isOpen, (open) => {
  if (!open) {
    cancelarForm.resetForm();
    shouldPrint.value = false;
  }
});

function handleClose() {
  cancelarForm.resetForm();
  shouldPrint.value = false;
  emit('close');
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
            {{ osDisplayNumber ? `Nº ${osDisplayNumber}` : 'Selecionada' }}
          </span>
        </p>
      </template>

      <div class="space-y-4">
        <BaseTextarea
          v-model="cancelarForm.motivo.value"
          label="Motivo do Cancelamento"
          placeholder="Informe o motivo..."
          :rows="3"
          :error="cancelarForm.errors.value.motivo"
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
            :is-loading="cancelarForm.isPending.value"
            class="flex-1"
            @click="cancelarForm.onSubmit"
          >
            CONFIRMAR
          </BaseButton>
        </div>
      </template>
    </ConfirmationTemplate>
  </BaseModal>
</template>
