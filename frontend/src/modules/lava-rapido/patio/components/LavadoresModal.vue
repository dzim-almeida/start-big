<script setup lang="ts">
/**
 * @component LavadoresModal
 * @description Troca os lavadores de um veículo no pátio (Spec 10B).
 * 1 ou 2 por carro (cliente, 12/11/2026); a comissão segue a regra do cargo
 * (Dividir/Inteira).
 */
import { ref, watch } from 'vue';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import SeletorLavadores from '../../shared/components/SeletorLavadores.vue';
import type { CartaoPatio } from '../../shared/schemas/patio.schema';

const props = defineProps<{ cartao: CartaoPatio | null; salvando?: boolean }>();
const emit = defineEmits<{ close: []; salvar: [ids: number[]] }>();

const ids = ref<number[]>([]);
watch(
  () => props.cartao,
  (cartao) => { ids.value = cartao ? cartao.lavadores.map((l) => l.funcionario_id) : []; },
  { immediate: true },
);
</script>

<template>
  <BaseModal :is-open="!!cartao" title="Lavadores" :subtitle="cartao?.placa ?? ''" size="sm" @close="emit('close')">
    <SeletorLavadores v-model="ids" />
    <template #footer>
      <div class="flex w-full justify-end gap-3">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :is-loading="salvando" @click="emit('salvar', ids)">Salvar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
