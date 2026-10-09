<script setup lang="ts">
/**
 * @component SugestaoStatusModal
 * @description A pergunta de status da OS (Spec 12B D12-D14; 12A D16).
 *
 * O backend só SUGERE: quem decide é o usuário. "Mover" grava só o status;
 * "Agora não" não muda nada, e a pergunta só volta na próxima mudança de
 * situação da produção. O nome do status vem do backend, no texto do
 * segmento ("Em Produção", "Aguardando Entrega"), nunca o código.
 */
import { computed } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import type { SugestaoStatus } from '@/modules/marcenaria/terceirizados/schemas/terceirizado.schema';

const props = defineProps<{ sugestao: SugestaoStatus; aplicando: boolean }>();
const emit = defineEmits<{ mover: []; agoraNao: [] }>();

/** O começo da frase: o que aconteceu na produção. */
const motivo = computed(() => {
  if (props.sugestao?.para === 'EM_ANDAMENTO') return 'A produção começou.';
  if (props.sugestao?.para === 'AGUARDANDO_RETIRADA') return 'Todos os móveis estão prontos.';
  return 'A produção mudou.';
});
</script>

<template>
  <BaseModal :is-open="sugestao !== null" title="Mudar o status da OS?" size="sm" overlay @close="emit('agoraNao')">
    <p v-if="sugestao" class="text-sm text-zinc-700" data-testid="pergunta-status">
      {{ motivo }} Mover a OS para <strong>{{ sugestao.rotulo }}</strong>?
    </p>
    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" :disabled="aplicando" data-testid="agora-nao" @click="emit('agoraNao')">Agora não</BaseButton>
        <BaseButton :is-loading="aplicando" data-testid="mover-status" @click="emit('mover')">Mover</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
