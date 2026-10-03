<script setup lang="ts">
/**
 * Pede o motivo antes de uma ação que fica no histórico (cancelar, voltar a
 * rascunho). O motivo é obrigatório no backend também — "quem cancelou o pedido
 * da Ambev, e por quê?" é a pergunta que o histórico existe para responder.
 */
import { computed, ref, watch } from 'vue';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

const props = defineProps<{
  aberto: boolean;
  titulo: string;
  descricao: string;
  confirmLabel: string;
  carregando?: boolean;
  perigo?: boolean;
}>();
const emit = defineEmits<{ fechar: []; confirmar: [motivo: string] }>();

const motivo = ref('');
watch(() => props.aberto, (aberto) => { if (aberto) motivo.value = ''; });

const valido = computed(() => motivo.value.trim().length >= 3);
</script>

<template>
  <BaseModal :is-open="aberto" :title="titulo" size="sm" overlay @close="emit('fechar')">
    <div class="flex flex-col gap-3">
      <p class="text-sm text-zinc-600">{{ descricao }}</p>
      <BaseTextarea v-model="motivo" label="Motivo" placeholder="Ex.: fornecedor sem estoque" :rows="3" required />
    </div>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <BaseButton variant="secondary" class="px-5" @click="emit('fechar')">Voltar</BaseButton>
        <BaseButton
          :variant="perigo ? 'danger' : 'primary'"
          class="px-5"
          :disabled="!valido"
          :is-loading="carregando"
          @click="emit('confirmar', motivo.trim())"
        >
          {{ confirmLabel }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
