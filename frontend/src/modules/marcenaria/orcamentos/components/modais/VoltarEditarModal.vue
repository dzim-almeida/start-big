<script setup lang="ts">
/**
 * @component VoltarEditarModal
 * @description Confirmação de "Voltar a editar" (Spec 06B D37; SPEC-00 T3c).
 * O valor já está com o cliente: o usuário precisa saber que vai ter de
 * enviar de novo.
 */
import { computed } from 'vue';

import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import { formatCurrency } from '@/shared/utils/finance';

const props = defineProps<{ isOpen: boolean; totalCentavos: number; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [] }>();

// Só número formatado entra no HTML (nada digitado pelo usuário).
const descricao = computed(
  () => `O cliente recebeu este orçamento com total de <strong>${formatCurrency(props.totalCentavos)}</strong>. `
    + 'Ao editar, ele volta para Rascunho e precisa ser enviado de novo.',
);
</script>

<template>
  <BaseConfirmModal
    :is-open="isOpen"
    title="Voltar a editar"
    :description="descricao"
    confirm-label="Voltar a editar"
    variant="warning"
    :is-loading="gravando"
    @close="emit('close')"
    @confirm="emit('confirmar')"
  />
</template>
