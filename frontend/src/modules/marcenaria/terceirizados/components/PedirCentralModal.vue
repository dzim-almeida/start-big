<script setup lang="ts">
/**
 * @component PedirCentralModal
 * @description "Pedir à central" com o módulo Compras (Spec 11B D4; 11A D9).
 *
 * Cria UM pedido de serviço, em rascunho, no Compras, para os móveis
 * marcados (todos da mesma central). Previsão e observação são opcionais. O
 * pedido é do Compras: enviar, receber e lançar a conta são feitos lá.
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { MovelTerceirizado } from '../schemas/terceirizado.schema';

const props = defineProps<{ isOpen: boolean; moveis: MovelTerceirizado[]; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [previsao: string | null, observacao: string | null] }>();

const previsao = ref('');
const observacao = ref('');

// Abriu: campos limpos (cada pedido é um pedido novo).
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  previsao.value = '';
  observacao.value = '';
}, { immediate: true });

/** A central é a mesma para todos (a barra de ações já garantiu, D3). */
const central = computed(() => props.moveis[0]?.central ?? null);

function confirmar() {
  if (props.gravando) return;                         // clique duplo não cria dois pedidos
  emit('confirmar', previsao.value || null, observacao.value.trim() || null);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Pedir à central" :subtitle="central?.nome" size="md" overlay @close="emit('close')">
    <div class="flex flex-col gap-4">
      <ul class="flex flex-col gap-1 text-sm text-zinc-700" data-testid="moveis-do-pedido">
        <li v-for="movel in moveis" :key="movel.movel_id">
          <strong>{{ movel.nome }}</strong> <span class="text-zinc-500">· {{ movel.ambiente }} · {{ movel.quantidade }}×</span>
        </li>
      </ul>

      <BaseDateInput v-model="previsao" label="Previsão de chegada" />
      <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
        Observação
        <textarea
          v-model="observacao"
          rows="2"
          maxlength="500"
          class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="observacao-pedido"
        />
      </label>

      <!-- E6b: quem manda no pedido é o Compras -->
      <p class="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-800" data-testid="aviso-rascunho">
        O pedido nasce como rascunho no Compras. Envie e receba por lá.
      </p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :is-loading="gravando" data-testid="confirmar-pedir" @click="confirmar">Criar pedido</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
