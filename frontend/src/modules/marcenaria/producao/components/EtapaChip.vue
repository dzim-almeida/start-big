<script setup lang="ts">
/**
 * @component EtapaChip
 * @description Uma etapa de produção como "chip" (Spec 12B D3, D4, D5).
 *
 * Cores para ler de longe, na tela da fábrica: cinza = pendente; azul = em
 * execução (com o nome de quem está fazendo); verde com ✓ = concluída. A
 * próxima etapa do móvel tem a borda destacada.
 *
 * - Clique no pendente ou em execução: CONCLUIR (o caso comum, um clique).
 * - Clique no concluído: menu com "Reabrir".
 * - Botão direito (ou o "⋯" que aparece ao passar o mouse): Iniciar, Concluir, Reabrir.
 * - No modo seleção, o clique só marca/desmarca.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { Check, MoreHorizontal } from 'lucide-vue-next';

import type { Etapa } from '../schemas/producao.schema';

const props = defineProps<{
  etapa: Etapa;
  /** É a próxima etapa do móvel (a primeira não concluída). */
  proxima: boolean;
  /** A OS aceita mudanças (12B D10). */
  editavel: boolean;
  /** Modo seleção (D5): o clique marca em vez de concluir. */
  modoSelecao: boolean;
  selecionada: boolean;
}>();

const emit = defineEmits<{
  concluir: [];
  iniciar: [];
  reabrir: [];
  alternar: [];
}>();

const menuAberto = ref(false);
const raiz = ref<HTMLElement | null>(null);
onClickOutside(raiz, () => { menuAberto.value = false; });

const concluida = computed(() => props.etapa.status === 'CONCLUIDA');
const emExecucao = computed(() => props.etapa.status === 'EM_EXECUCAO');

/** As opções do menu, só as que fazem sentido agora. */
const opcoes = computed(() => {
  const lista: { id: 'iniciar' | 'concluir' | 'reabrir'; texto: string }[] = [];
  if (props.etapa.status === 'PENDENTE') lista.push({ id: 'iniciar', texto: 'Iniciar…' });
  if (!concluida.value) lista.push({ id: 'concluir', texto: 'Concluir' });
  if (props.etapa.status !== 'PENDENTE') lista.push({ id: 'reabrir', texto: 'Reabrir' });
  return lista;
});

/** O clique principal (D4). */
function clicar() {
  if (!props.editavel) return;
  if (props.modoSelecao) {
    emit('alternar');
    return;
  }
  if (concluida.value) menuAberto.value = !menuAberto.value;   // concluída: o menu com "Reabrir"
  else emit('concluir');
}

/** Botão direito: o menu completo. */
function abrirMenu() {
  if (props.editavel && !props.modoSelecao) menuAberto.value = true;
}

function escolher(id: 'iniciar' | 'concluir' | 'reabrir') {
  menuAberto.value = false;
  if (id === 'iniciar') emit('iniciar');
  else if (id === 'concluir') emit('concluir');
  else emit('reabrir');
}

/** A dica do `title`: o que o clique faz. */
const dica = computed(() => {
  if (!props.editavel) return undefined;
  if (props.modoSelecao) return 'Clique para marcar';
  return concluida.value ? 'Clique para reabrir' : 'Clique para concluir · botão direito: mais opções';
});
</script>

<template>
  <div ref="raiz" class="group relative inline-flex">
    <button
      type="button"
      class="inline-flex min-h-10 items-center gap-1.5 rounded-full border-2 px-3.5 py-1.5 text-sm font-semibold transition-colors"
      :class="[
        concluida ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
        : emExecucao ? 'border-blue-200 bg-blue-50 text-blue-800'
          : 'border-zinc-200 bg-zinc-50 text-zinc-600',
        proxima && !concluida ? 'border-brand-primary' : '',
        selecionada ? 'ring-2 ring-offset-1 ring-brand-primary' : '',
        editavel ? 'cursor-pointer hover:brightness-95' : 'cursor-default',
      ]"
      :title="dica"
      :aria-pressed="modoSelecao ? selecionada : undefined"
      :data-testid="`chip-${etapa.id}`"
      :data-status="etapa.status"
      @click="clicar"
      @contextmenu.prevent="abrirMenu"
    >
      <Check v-if="concluida" :size="16" />
      <span v-else-if="emExecucao" class="h-2 w-2 rounded-full bg-blue-500" aria-hidden="true" />
      {{ etapa.nome }}
      <!-- D3: em execução mostra quem está fazendo -->
      <span v-if="emExecucao && etapa.responsavel" class="font-normal">· {{ etapa.responsavel }}</span>
    </button>

    <!-- O "⋯": o mesmo menu do botão direito, para quem não usa o botão direito -->
    <button
      v-if="editavel && !modoSelecao"
      type="button"
      class="absolute -right-1 -top-1 hidden h-5 w-5 items-center justify-center rounded-full border border-zinc-200 bg-white text-zinc-500 shadow-sm group-hover:flex cursor-pointer"
      aria-label="Mais opções da etapa"
      :data-testid="`menu-chip-${etapa.id}`"
      @click.stop="menuAberto = !menuAberto"
    >
      <MoreHorizontal :size="12" />
    </button>

    <div v-if="menuAberto" role="menu" class="absolute left-0 top-full z-30 mt-1 w-40 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
      <button
        v-for="opcao in opcoes"
        :key="opcao.id"
        type="button"
        role="menuitem"
        class="block w-full px-3 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 cursor-pointer"
        :data-testid="`opcao-${opcao.id}`"
        @click="escolher(opcao.id)"
      >
        {{ opcao.texto }}
      </button>
    </div>
  </div>
</template>
