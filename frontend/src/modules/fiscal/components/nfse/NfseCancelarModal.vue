<script setup lang="ts">
/**
 * @component NfseCancelarModal
 * @description Cancelar uma NFS-e autorizada. O prazo é de cada município: quem
 * recusa fora dele é o Sistema Nacional, com a mensagem dele.
 */
import { computed, ref, watch } from 'vue';
import { Ban } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

import { useNfseCancelarMutation } from '../../composables/useNfse';
import type { NfseDocumento } from '../../types/fiscal.types';

const props = defineProps<{ documento: NfseDocumento | null }>();
const emit = defineEmits<{ close: [] }>();

/** 15 caracteres: exigência do cancelamento, não escolha nossa. */
const MIN_CHARS = 15;
const justificativa = ref('');
const cancelarMutation = useNfseCancelarMutation();

watch(() => props.documento, () => (justificativa.value = ''));

const valida = computed(() => justificativa.value.trim().length >= MIN_CHARS);

async function cancelar() {
  if (!props.documento || !valida.value) return;
  await cancelarMutation.mutateAsync({ id: props.documento.id, justificativa: justificativa.value.trim() });
  emit('close');
}
</script>

<template>
  <BaseModal :is-open="!!documento" title="Cancelar NFS-e" size="md" @close="emit('close')">
    <div class="space-y-4">
      <p class="text-sm text-zinc-600">
        NFS-e nº <strong>{{ documento?.numero ?? '—' }}</strong> da OS {{ documento?.numero_os }}.
        O cancelamento não pode ser desfeito.
      </p>
      <BaseTextarea
        v-model="justificativa"
        label="Justificativa"
        :rows="3"
        placeholder="Ex: serviço lançado em duplicidade"
        required
      />
      <p class="text-xs" :class="valida ? 'text-zinc-400' : 'text-amber-600'">
        {{ justificativa.trim().length }}/{{ MIN_CHARS }} caracteres no mínimo
      </p>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <BaseButton type="button" variant="secondary" @click="emit('close')">Voltar</BaseButton>
        <BaseButton
          type="button"
          variant="danger"
          :disabled="!valida || cancelarMutation.isPending.value"
          :is-loading="cancelarMutation.isPending.value"
          @click="cancelar"
        >
          <Ban :size="16" class="mr-1.5" />
          Cancelar NFS-e
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
