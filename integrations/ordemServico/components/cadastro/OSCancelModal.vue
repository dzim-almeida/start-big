<!--
===========================================================================
ARQUIVO: OSCancelModal.vue
MODULO: Ordem de Servico
DESCRICAO: Modal de confirmacao para cancelamento de Ordem de Servico.
           Exige motivo obrigatorio e oferece opcao de impressao.
===========================================================================

PROPS:
- isOpen: Controla visibilidade do modal
- os: Ordem de Servico a ser cancelada
- isLoading: Estado de carregamento da acao

EMITS:
- close: Fecha o modal
- confirm: Confirma cancelamento com { motivo, print }

DEPENDENCIAS:
- useOSCancel: Gerencia estado e validacao do formulario
- ConfirmationTemplate: Template padrao de confirmacao
===========================================================================
-->
<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import BaseTextarea from '@/shared/components/commons/BaseInput/BaseTextarea.vue';
import BaseCheckbox from '@/shared/components/commons/BaseCheckbox/BaseCheckbox.vue';
import ConfirmationTemplate from '@/shared/components/templates/ConfirmationTemplate.vue';
import { AlertTriangle } from 'lucide-vue-next';
import { useOSCancel } from '../../composables/useOSCancel';
import type { OrdemServicoListRead } from '../../types/ordemServico.types';

interface Props {
  isOpen: boolean;
  os: OrdemServicoListRead | null;
  isLoading?: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  confirm: [payload: { motivo: string; print: boolean }];
}>();

// Utils
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

       <!-- Slot Default: Formulario -->
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
