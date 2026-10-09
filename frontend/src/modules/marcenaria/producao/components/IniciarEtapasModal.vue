<script setup lang="ts">
/**
 * @component IniciarEtapasModal
 * @description "Iniciar" uma ou mais etapas escolhendo QUEM vai fazer
 * (Spec 12B D4, D5; 12A D7). Já vem com o "Feito por" do topo da aba.
 */
import { ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { OpcaoFuncionario } from '../utils/producao';

const props = defineProps<{
  isOpen: boolean;
  /** "Furação — Balcão" ou "3 etapas". */
  descricao: string;
  funcionarios: OpcaoFuncionario[];
  /** O "Feito por" atual (null = o usuário logado). */
  responsavelInicial: number | null;
  gravando: boolean;
}>();
const emit = defineEmits<{ close: []; confirmar: [responsavelId: number | null] }>();

/** '' = o usuário logado (o <select> nativo não guarda null). */
const escolhido = ref('');
watch(() => props.isOpen, (aberto) => {
  if (aberto) escolhido.value = props.responsavelInicial ? String(props.responsavelInicial) : '';
}, { immediate: true });

function confirmar() {
  if (props.gravando) return;
  emit('confirmar', escolhido.value ? Number(escolhido.value) : null);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Iniciar etapa" :subtitle="descricao" size="sm" overlay @close="emit('close')">
    <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
      Quem vai fazer
      <select
        v-model="escolhido"
        class="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base text-zinc-800 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        data-testid="responsavel-iniciar"
      >
        <option value="">Eu (usuário logado)</option>
        <option v-for="f in funcionarios" :key="f.id" :value="String(f.id)">{{ f.nome }}</option>
      </select>
    </label>
    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :is-loading="gravando" data-testid="confirmar-iniciar" @click="confirmar">Iniciar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
