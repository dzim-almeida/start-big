<script setup lang="ts">
/**
 * @component ResolverPendenciaModal
 * @description "Resolver" uma pendência: como foi resolvida e quando
 * (Spec 13B D7; 13A D6). Quem resolveu fica gravado pelo backend.
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { hojeIso } from '@/modules/marcenaria/terceirizados/utils/terceirizados';

import type { Pendencia } from '../schemas/entrega.schema';

const props = defineProps<{ isOpen: boolean; pendencia: Pendencia | null; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [resolucao: string, data: string | null] }>();

const resolucao = ref('');
const data = ref('');

// Abriu: a resolução em branco e a data de hoje.
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  resolucao.value = '';
  data.value = hojeIso();
}, { immediate: true });

const erroData = computed(() => (data.value && data.value > hojeIso() ? 'A data não pode ser no futuro.' : ''));
const valido = computed(() => resolucao.value.trim().length > 0 && !erroData.value);

function confirmar() {
  if (!valido.value || props.gravando) return;
  emit('confirmar', resolucao.value.trim(), data.value || null);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Resolver pendência" :subtitle="pendencia?.descricao" size="sm" overlay @close="emit('close')">
    <div class="flex flex-col gap-3">
      <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
        Como foi resolvida?
        <textarea
          v-model="resolucao"
          rows="2"
          maxlength="300"
          class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="resolucao"
        />
      </label>
      <BaseDateInput v-model="data" label="Resolvida em" :error="erroData" />
    </div>
    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="!valido" :is-loading="gravando" data-testid="confirmar-resolver" @click="confirmar">Resolver</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
