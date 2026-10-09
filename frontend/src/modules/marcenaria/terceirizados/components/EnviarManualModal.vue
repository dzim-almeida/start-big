<script setup lang="ts">
/**
 * @component EnviarManualModal
 * @description "Enviar pedido" SEM o módulo Compras (Spec 11B D6; 11A D3).
 *
 * Só anota que o pedido saiu: o número que a central deu e quando deve
 * chegar (os dois opcionais). Nada é criado em outro módulo.
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { MovelTerceirizado } from '../schemas/terceirizado.schema';

const props = defineProps<{ isOpen: boolean; moveis: MovelTerceirizado[]; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [pedido: string | null, previsao: string | null] }>();

const pedido = ref('');
const previsao = ref('');

// Abriu: campos limpos.
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  pedido.value = '';
  previsao.value = '';
}, { immediate: true });

const central = computed(() => props.moveis[0]?.central ?? null);

function confirmar() {
  if (props.gravando) return;
  emit('confirmar', pedido.value.trim() || null, previsao.value || null);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Enviar pedido à central" :subtitle="central?.nome" size="md" overlay @close="emit('close')">
    <form class="flex flex-col gap-4" @submit.prevent="confirmar">
      <ul class="flex flex-col gap-1 text-sm text-zinc-700">
        <li v-for="movel in moveis" :key="movel.movel_id">
          <strong>{{ movel.nome }}</strong> <span class="text-zinc-500">· {{ movel.ambiente }} · {{ movel.quantidade }}×</span>
        </li>
      </ul>

      <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
        Nº do pedido na central
        <input
          v-model="pedido"
          type="text"
          maxlength="60"
          autocomplete="off"
          class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="numero-pedido"
        />
      </label>
      <BaseDateInput v-model="previsao" label="Previsão de chegada" />
      <button type="submit" class="hidden" aria-hidden="true" tabindex="-1" />
    </form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :is-loading="gravando" data-testid="confirmar-enviar" @click="confirmar">Anotar envio</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
