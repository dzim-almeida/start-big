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
import { CheckCircle2, Circle, MoreHorizontal, RefreshCw } from 'lucide-vue-next';

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
  <div ref="raiz" class="group relative flex">
    <button
      type="button"
      class="flex min-h-16 w-full items-start gap-2.5 rounded-xl border px-3.5 py-3 text-left transition-colors"
      :class="[
        concluida ? 'border-emerald-200 bg-white'
        : emExecucao ? 'border-2 border-brand-primary bg-brand-primary-light'
          : 'border-zinc-200 bg-white',
        proxima && !concluida && !emExecucao ? 'border-brand-primary/50' : '',
        selecionada ? 'ring-2 ring-offset-1 ring-brand-primary' : '',
        editavel ? 'cursor-pointer hover:brightness-[0.98]' : 'cursor-default',
      ]"
      :title="dica"
      :aria-pressed="modoSelecao ? selecionada : undefined"
      :data-testid="`chip-${etapa.id}`"
      :data-status="etapa.status"
      @click="clicar"
      @contextmenu.prevent="abrirMenu"
    >
      <CheckCircle2 v-if="concluida" :size="18" class="mt-0.5 shrink-0 text-emerald-600" aria-hidden="true" />
      <RefreshCw v-else-if="emExecucao" :size="18" class="mt-0.5 shrink-0 text-brand-primary" aria-hidden="true" />
      <Circle v-else :size="18" class="mt-0.5 shrink-0 text-zinc-300" aria-hidden="true" />
      <span class="min-w-0">
        <span
          class="block text-sm font-semibold"
          :class="concluida ? 'text-emerald-800' : emExecucao ? 'text-brand-primary' : 'text-zinc-600'"
        >
          {{ etapa.nome }}
        </span>
        <span class="block truncate text-xs" :class="concluida ? 'text-emerald-700' : emExecucao ? 'text-brand-primary' : 'text-zinc-500'">
          <template v-if="concluida">Concluída<template v-if="etapa.concluida_por || etapa.responsavel"> · {{ etapa.concluida_por || etapa.responsavel }}</template></template>
          <!-- D3: em execução mostra quem está fazendo -->
          <template v-else-if="emExecucao">Em execução<template v-if="etapa.responsavel"> · {{ etapa.responsavel }}</template></template>
          <template v-else>{{ proxima ? 'Próxima' : 'Aguardando' }}</template>
        </span>
      </span>
    </button>

    <!-- O "⋯": o mesmo menu do botão direito, para quem não usa o botão direito -->
    <button
      v-if="editavel && !modoSelecao"
      type="button"
      class="absolute right-1.5 top-1.5 hidden h-6 w-6 items-center justify-center rounded-full border border-zinc-200 bg-white text-zinc-500 shadow-sm group-hover:flex cursor-pointer"
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
