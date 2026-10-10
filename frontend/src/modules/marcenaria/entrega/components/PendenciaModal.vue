<script setup lang="ts">
/**
 * @component PendenciaModal
 * @description "+ Pendência" num ambiente já entregue (Spec 13B D7; 13A D6).
 * Vale até com a OS finalizada: o cliente liga na semana seguinte.
 */
import { computed, nextTick, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

const props = defineProps<{ isOpen: boolean; ambiente: string; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [descricao: string] }>();

const texto = ref('');
const campo = ref<HTMLTextAreaElement | null>(null);

// Abriu: campo vazio e focado.
watch(() => props.isOpen, async (aberto) => {
  if (!aberto) return;
  texto.value = '';
  await nextTick();
  campo.value?.focus();
}, { immediate: true });

const valido = computed(() => texto.value.trim().length > 0);

function confirmar() {
  if (!valido.value || props.gravando) return;
  emit('confirmar', texto.value.trim());
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Nova pendência" :subtitle="ambiente" size="sm" overlay @close="emit('close')">
    <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
      O que ficou por fazer?
      <textarea
        ref="campo"
        v-model="texto"
        rows="3"
        maxlength="300"
        class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        data-testid="descricao-pendencia"
      />
    </label>
    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="!valido" :is-loading="gravando" data-testid="confirmar-pendencia" @click="confirmar">Anotar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
