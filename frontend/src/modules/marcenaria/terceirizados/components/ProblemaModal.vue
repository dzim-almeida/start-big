<script setup lang="ts">
/**
 * @component ProblemaModal
 * @description "Registrar problema" num móvel que chegou (Spec 11B D7; 11A D4).
 *
 * O móvel fica "Recebido com problema" (não está pronto) até alguém
 * conferir de novo depois que a central resolver.
 */
import { computed, nextTick, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { MovelTerceirizado } from '../schemas/terceirizado.schema';

const props = defineProps<{ isOpen: boolean; movel: MovelTerceirizado | null; gravando: boolean }>();
const emit = defineEmits<{ close: []; confirmar: [texto: string] }>();

const texto = ref('');
const campo = ref<HTMLTextAreaElement | null>(null);

// Abriu: o problema já registrado (para corrigir) ou vazio; campo focado.
watch(() => props.isOpen, async (aberto) => {
  if (!aberto) return;
  texto.value = props.movel?.problema ?? '';
  await nextTick();
  campo.value?.focus();
}, { immediate: true });

/** Só espaços não descreve problema nenhum (o backend também recusa). */
const valido = computed(() => texto.value.trim().length > 0);

function confirmar() {
  if (!valido.value || props.gravando) return;
  emit('confirmar', texto.value.trim());
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Registrar problema" :subtitle="movel?.nome" size="sm" overlay @close="emit('close')">
    <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
      O que veio errado?
      <textarea
        ref="campo"
        v-model="texto"
        rows="3"
        maxlength="500"
        placeholder="Ex.: porta riscada, medida errada"
        class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        data-testid="texto-problema"
      />
    </label>
    <p class="mt-2 text-xs text-zinc-500">O móvel fica como "Recebido com problema" até ser conferido de novo.</p>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="!valido" :is-loading="gravando" data-testid="confirmar-problema" @click="confirmar">Registrar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
