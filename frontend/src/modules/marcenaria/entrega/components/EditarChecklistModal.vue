<script setup lang="ts">
/**
 * @component EditarChecklistModal
 * @description O checklist de vistoria de UM ambiente (Spec 13B D8; 13A D2).
 *
 * Mesmo editor de listas de Configurações › Marcenaria, com as mesmas regras
 * (1 a 30 itens, até 120 caracteres, sem repetir). Só enquanto a entrega do
 * ambiente está pendente: a cozinha tem "cooktop nivelado"; o closet não.
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import ListaTextosEditavel from '@/shared/components/ui/ListaTextosEditavel/ListaTextosEditavel.vue';
import { errosDosItens } from '@/shared/components/ui/ListaTextosEditavel/errosDosItens';

import type { EntregaAmbiente } from '../schemas/entrega.schema';

/** Os mesmos limites do checklist da configuração (04A). */
const MAX_ITENS = 30;
const MAX_CARACTERES = 120;

const props = defineProps<{ isOpen: boolean; entrega: EntregaAmbiente | null; gravando: boolean }>();
const emit = defineEmits<{ close: []; salvar: [itens: string[]] }>();

const itens = ref<string[]>([]);

// Abriu: o checklist atual do ambiente (só os textos).
watch(() => props.isOpen, (aberto) => {
  if (aberto && props.entrega) itens.value = props.entrega.checklist.map((i) => i.texto);
}, { immediate: true });

const temErro = computed(() => !itens.value.length || errosDosItens(itens.value, MAX_CARACTERES).some(Boolean));

function salvar() {
  if (temErro.value || props.gravando) return;
  emit('salvar', itens.value.map((i) => i.trim()));
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Editar checklist" :subtitle="entrega?.ambiente" size="md" overlay @close="emit('close')">
    <ListaTextosEditavel v-model="itens" :max-itens="MAX_ITENS" :max-caracteres="MAX_CARACTERES" rotulo-item="item do checklist" />
    <p class="mt-3 text-xs text-zinc-500">Vale só para este ambiente. O padrão fica em Configurações › Marcenaria.</p>
    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="temErro" :is-loading="gravando" data-testid="salvar-checklist" @click="salvar">Salvar checklist</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
