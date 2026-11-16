<script setup lang="ts">
/**
 * @component ReceberManualModal
 * @description "Receber" SEM o módulo Compras (Spec 11B D6; 11A D3).
 *
 * Anota a data em que os móveis chegaram (já vem com hoje). Conferir é o
 * passo seguinte, separado: chegar não é o mesmo que estar bom.
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { MovelTerceirizado } from '../schemas/terceirizado.schema';
import { hojeIso } from '../utils/terceirizados';

const props = defineProps<{ isOpen: boolean; moveis: MovelTerceirizado[]; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [data: string | null] }>();

const data = ref('');

// Abriu: a data de hoje (o caso comum: o caminhão está na porta).
watch(() => props.isOpen, (aberto) => {
  if (aberto) data.value = hojeIso();
}, { immediate: true });

/** A chegada não pode ser no futuro. */
const erro = computed(() => (data.value && data.value > hojeIso() ? 'A data da chegada não pode ser no futuro.' : ''));

function confirmar() {
  if (props.gravando || erro.value) return;
  emit('confirmar', data.value || null);              // vazio = o backend usa hoje
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Receber da central" :subtitle="moveis[0]?.central?.nome" size="sm" overlay @close="emit('close')">
    <div class="flex flex-col gap-4">
      <ul class="flex flex-col gap-1 text-sm text-zinc-700">
        <li v-for="movel in moveis" :key="movel.movel_id"><strong>{{ movel.nome }}</strong> · {{ movel.quantidade }}×</li>
      </ul>
      <BaseDateInput v-model="data" label="Chegou em" :error="erro" />
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="!!erro" :is-loading="gravando" data-testid="confirmar-receber" @click="confirmar">Anotar chegada</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
