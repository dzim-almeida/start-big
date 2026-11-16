<script setup lang="ts">
/**
 * @component RecusarModal
 * @description Registrar a recusa do cliente (Spec 06B D38; 06A D17).
 * Motivo obrigatório (até 500), com atalhos que PREENCHEM o texto ("Preço",
 * "Prazo"...) e campo livre: padroniza para relatórios sem tirar a liberdade.
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

import { ATALHOS_RECUSA, LIMITES } from '../../constants/orcamento.constants';

const props = defineProps<{ isOpen: boolean; gravando: boolean }>();
const emit = defineEmits<{ close: []; recusar: [motivo: string] }>();

const motivo = ref<string | null>('');

// Abriu de novo: começa limpo.
watch(() => props.isOpen, (aberto) => { if (aberto) motivo.value = ''; }, { immediate: true });

const texto = computed(() => (motivo.value ?? '').trim());
const erro = computed(() => (texto.value.length > LIMITES.motivoRecusa ? `O motivo aceita até ${LIMITES.motivoRecusa} caracteres.` : ''));
</script>

<template>
  <BaseModal :is-open="isOpen" title="Recusar orçamento" subtitle="O cliente não aceitou esta proposta." size="md" @close="emit('close')">
    <p class="mb-2 text-xs font-medium text-zinc-600">Motivo</p>
    <div class="mb-3 flex flex-wrap gap-2">
      <button
        v-for="atalho in ATALHOS_RECUSA"
        :key="atalho"
        type="button"
        class="rounded-full border px-3 py-1 text-xs cursor-pointer"
        :class="texto === atalho ? 'border-brand-primary bg-brand-primary text-white' : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50'"
        @click="motivo = atalho"
      >
        {{ atalho }}
      </button>
    </div>
    <BaseTextarea v-model="motivo" placeholder="Ou escreva o motivo" :rows="3" :error="erro" />

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton
          variant="danger"
          :disabled="!texto || !!erro"
          :is-loading="gravando"
          data-testid="confirmar-recusa"
          @click="emit('recusar', texto)"
        >
          Registrar recusa
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
