<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
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
    :title="showAdiantamento ? 'Adiantamento recebido' : 'Cancelar OS'"
    size="sm"
    @close="handleClose"
  >
    <!-- ── Passo 1: Confirmação de cancelamento ── -->
    <template v-if="!showAdiantamento">
      <div class="flex items-start gap-3 p-3 bg-red-50 border border-red-100 rounded-xl mb-4">
        <AlertTriangle :size="18" class="text-red-500 shrink-0 mt-0.5" />
        <p class="text-sm text-red-700 leading-snug">
          Tem certeza que deseja cancelar a OS
          <span class="font-bold">{{ osDisplayNumber ?? osNumero }}</span>?
        </p>
      </div>

      <div class="space-y-3">
        <BaseTextarea
          v-model="cancelarForm.motivo.value"
          label="Motivo do cancelamento"
          placeholder="Informe o motivo..."
          :rows="3"
          :error="cancelarForm.errors.value.motivo"
        />
        <BaseCheckbox v-model="shouldPrint" label="Imprimir comprovante de cancelamento" />
      </div>
    </template>

    <!-- ── Passo 2: O que fazer com o adiantamento ── -->
    <template v-else>
      <div class="flex flex-col items-center gap-4 py-2">
        <div class="p-3 bg-amber-50 rounded-full">
          <Banknote :size="28" class="text-amber-500" />
        </div>
        <div class="text-center">
          <p class="text-sm font-semibold text-zinc-800">
            Adiantamento de <span class="text-amber-600">{{ formatCurrency(props.valorEntrada ?? 0) }}</span>
          </p>
          <p class="text-xs text-zinc-500 mt-0.5">O que deseja fazer com esse valor?</p>
        </div>
        <div class="grid grid-cols-2 gap-3 w-full">
          <button
            type="button"
            class="flex flex-col items-center gap-2 p-3 rounded-xl border-2 border-emerald-400 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-all cursor-pointer"
            @click="handleConfirmarPasso2(false)"
          >
            <BookmarkCheck :size="18" />
            <span class="text-xs font-semibold text-center leading-tight">Manter como<br>crédito</span>
          </button>
          <button
            type="button"
            class="flex flex-col items-center gap-2 p-3 rounded-xl border-2 border-brand-primary bg-brand-primary/5 text-brand-primary hover:bg-brand-primary/10 transition-all cursor-pointer"
            :disabled="cancelarForm.isPending.value"
            @click="handleConfirmarPasso2(true)"
          >
            <Banknote :size="18" />
            <span class="text-xs font-semibold text-center leading-tight">Devolver em<br>dinheiro</span>
          </button>
        </div>
        <BaseCheckbox v-model="shouldPrint" label="Imprimir comprovante" />
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <BaseButton variant="secondary" class="px-5" @click="handleClose">
          Voltar
        </BaseButton>
        <BaseButton
          v-if="!showAdiantamento"
          class="px-5 bg-red-500 hover:bg-red-600 border-red-500 text-white"
          :is-loading="cancelarForm.isPending.value"
          @click="handleConfirmarPasso1"
        >
          Confirmar cancelamento
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
