<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import ConfirmationTemplate from '@/shared/components/templates/ConfirmationTemplate.vue';
import { AlertTriangle, Banknote, BookmarkCheck } from 'lucide-vue-next';
import { useOSCancelarForm } from '../composables/form/useOSCancelar.form';
import { formatCurrency } from '@/shared/utils/finance';

interface Props {
  isOpen: boolean;
  osNumero: string | null;
  osDisplayNumber?: string;
  valorEntrada?: number;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  cancelled: [payload: { shouldPrint: boolean }];
}>();

const showAdiantamento = ref(false);
const shouldPrint = ref(false);

const temAdiantamento = computed(() => (props.valorEntrada ?? 0) > 0);
const osNumberRef = computed(() => props.osNumero);

const cancelarForm = useOSCancelarForm({
  osNumber: osNumberRef,
  onSuccess: () => {
    emit('cancelled', { shouldPrint: shouldPrint.value });
  },
});

watch(() => props.isOpen, (open) => {
  if (!open) {
    showAdiantamento.value = false;
    cancelarForm.resetForm();
    shouldPrint.value = false;
  }
});

function handleClose() {
  showAdiantamento.value = false;
  cancelarForm.resetForm();
  shouldPrint.value = false;
  emit('close');
}

function handleConfirmarPasso1() {
  if (temAdiantamento.value) {
    showAdiantamento.value = true;
  } else {
    cancelarForm.onSubmit();
  }
}

function handleConfirmarPasso2(devolver: boolean) {
  cancelarForm.submitDireto(devolver);
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="showAdiantamento ? 'Adiantamento recebido' : 'Cancelar O.S.?'"
    size="sm"
    @close="handleClose"
  >
    <!-- ── Passo 1: Confirmação de cancelamento ── -->
    <ConfirmationTemplate
      v-if="!showAdiantamento"
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
          <BaseCheckbox v-model="shouldPrint" label="Imprimir Comprovante" />
        </div>
      </div>

      <template #footer>
        <div class="flex gap-3 w-full">
          <BaseButton variant="secondary" class="flex-1" @click="handleClose">
            VOLTAR
          </BaseButton>
          <BaseButton variant="primary" class="flex-1" @click="handleConfirmarPasso1">
            CONFIRMAR
          </BaseButton>
        </div>
      </template>
    </ConfirmationTemplate>

    <!-- ── Passo 2: O que fazer com o adiantamento ── -->
    <div v-else class="flex flex-col items-center gap-5 py-2">
      <div class="p-4 bg-amber-50 rounded-full">
        <Banknote :size="32" class="text-amber-500" />
      </div>

      <div class="text-center space-y-1">
        <p class="text-sm font-semibold text-zinc-800">
          Esta OS tinha um adiantamento de
          <span class="text-amber-600">{{ formatCurrency(props.valorEntrada ?? 0) }}</span>
        </p>
        <p class="text-xs text-zinc-500">O que deseja fazer com esse valor?</p>
      </div>

      <div class="grid grid-cols-2 gap-3 w-full">
        <button
          type="button"
          class="flex flex-col items-center gap-2 p-3.5 rounded-xl border-2 border-emerald-400 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-all"
          @click="handleConfirmarPasso2(false)"
        >
          <BookmarkCheck :size="20" />
          <span class="text-xs font-semibold text-center leading-tight">Manter como<br>crédito</span>
        </button>
        <button
          type="button"
          class="flex flex-col items-center gap-2 p-3.5 rounded-xl border-2 border-brand-primary bg-brand-primary/5 text-brand-primary hover:bg-brand-primary/10 transition-all"
          :disabled="cancelarForm.isPending.value"
          @click="handleConfirmarPasso2(true)"
        >
          <Banknote :size="20" />
          <span class="text-xs font-semibold text-center leading-tight">Devolver em<br>dinheiro</span>
        </button>
      </div>

      <div class="flex justify-center">
        <BaseCheckbox v-model="shouldPrint" label="Imprimir Comprovante" />
      </div>

      <button
        type="button"
        class="text-xs text-zinc-400 hover:text-zinc-600 transition-colors"
        @click="showAdiantamento = false"
      >
        ← Voltar
      </button>
    </div>

    <template #footer><span></span></template>
  </BaseModal>
</template>
