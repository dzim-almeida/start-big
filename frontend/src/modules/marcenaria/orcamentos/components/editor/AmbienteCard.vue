<script setup lang="ts">
/**
 * @component AmbienteCard
 * @description Um ambiente do orçamento (Spec 06B D19, D20, §6.2) como GRUPO
 * da tabela "Ambientes e móveis" (redesign 10/2026): a linha do ambiente
 * (recolhível, com custo, subtotal BRUTO, "+ Móvel" e o menu "⋯": renomear,
 * subir, descer, excluir) e, embaixo, as linhas dos móveis.
 *
 * Toda ação grava na hora pela fila (D8): não há "salvar" para ambiente.
 */
import { computed, nextTick, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { ChevronDown, MoreHorizontal, Plus } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';

import { LIMITES } from '../../constants/orcamento.constants';
import { useEditor } from '../../composables/useEditorContexto';
import type { AmbienteDetalhe, MovelDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { escaparHtml } from '../../utils/textoSeguro';
import MovelLinha from './MovelLinha.vue';
import { gradeMoveis } from './gradeMoveis';

const props = defineProps<{
  ambiente: AmbienteDetalhe;
  /** Posição na lista (1, 2, 3…), mostrada como "01". */
  numero: number;
  primeiro: boolean;
  ultimo: boolean;
}>();

const emit = defineEmits<{ subir: []; descer: [] }>();

const { editavel, incluiCustos, acoesOrcamento, confirmar, abrirMovel } = useEditor();

/** Custo do ambiente: só vem para quem vê custos (06A D23). */
const custoAmbiente = computed(() => ('custo_centavos' in props.ambiente ? props.ambiente.custo_centavos : null));

const aberto = ref(true);                                 // cartão recolhível
const menuAberto = ref(false);
const menuRef = ref<HTMLElement | null>(null);
onClickOutside(menuRef, () => { menuAberto.value = false; });   // clicar fora fecha o menu

// --- Renomear -----------------------------------------------------------------
const renomeando = ref(false);
const novoNome = ref('');
const campoNome = ref<HTMLInputElement | null>(null);

async function comecarRenomear() {
  menuAberto.value = false;
  novoNome.value = props.ambiente.nome;
  renomeando.value = true;
  await nextTick();
  campoNome.value?.focus();                                // foco no nome (§7.12)
  campoNome.value?.select();
}

async function concluirRenomear() {
  if (!renomeando.value) return;                           // Enter e o "blur" logo depois: grava uma vez só
  const nome = novoNome.value.trim();
  renomeando.value = false;
  if (!nome || nome === props.ambiente.nome) return;       // nada mudou
  await acoesOrcamento.renomearAmbiente(props.ambiente.id, nome);
}

// --- Excluir --------------------------------------------------------------------
async function excluirAmbiente() {
  menuAberto.value = false;
  const qtd = props.ambiente.moveis.length;
  const nome = escaparHtml(props.ambiente.nome);           // o modal mostra HTML
  const ok = await confirmar({
    titulo: 'Excluir ambiente',
    descricao: qtd
      ? `Excluir o ambiente <strong>${nome}</strong> e ${qtd === 1 ? 'o móvel dele' : `os ${qtd} móveis dele`}?`
      : `Excluir o ambiente <strong>${nome}</strong>?`,
    confirmLabel: 'Excluir',
    variant: 'danger',
  });
  if (ok) await acoesOrcamento.removerAmbiente(props.ambiente.id);
}

// --- Móveis ---------------------------------------------------------------------
const moveis = computed(() => props.ambiente.moveis);

/** Troca o móvel de lugar com o vizinho e manda a nova ordem (D20). */
async function moverMovel(indice: number, direcao: -1 | 1) {
  const ids = moveis.value.map((m) => m.id);
  const alvo = indice + direcao;
  if (alvo < 0 || alvo >= ids.length) return;
  [ids[indice], ids[alvo]] = [ids[alvo], ids[indice]];
  await acoesOrcamento.ordenarMoveis(props.ambiente.id, ids);
}

async function excluirMovel(movel: MovelDetalhe) {
  const ok = await confirmar({
    titulo: 'Excluir móvel',
    descricao: `Excluir o móvel <strong>${escaparHtml(movel.nome)}</strong>?`,
    confirmLabel: 'Excluir',
    variant: 'danger',
  });
  if (ok) await acoesOrcamento.removerMovel(movel.id);
}

const CLASSE_ITEM_MENU = 'block w-full px-3 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 disabled:opacity-40 cursor-pointer';
</script>

<template>
  <div :data-testid="`ambiente-${ambiente.id}`">
    <!-- A linha do ambiente -->
    <div :class="['flex flex-wrap items-center gap-x-3 gap-y-2 border-y border-zinc-100 bg-zinc-50/80 px-4 py-2.5 md:items-center', gradeMoveis(incluiCustos)]">
      <div class="flex min-w-0 flex-1 items-center gap-3 md:col-span-4">
      <button
        type="button"
        class="rounded p-1 text-zinc-400 hover:bg-zinc-200/60 cursor-pointer"
        :aria-expanded="aberto"
        :aria-label="aberto ? `Recolher ${ambiente.nome}` : `Abrir ${ambiente.nome}`"
        @click="aberto = !aberto"
      >
        <ChevronDown :size="16" class="transition-transform" :class="aberto ? '' : '-rotate-90'" />
      </button>
      <span class="rounded-md bg-brand-primary-light px-1.5 py-0.5 text-xs font-bold tabular-nums text-brand-primary" aria-hidden="true">
        {{ String(numero).padStart(2, '0') }}
      </span>

      <div class="min-w-0 flex-1">
        <input
          v-if="renomeando"
          ref="campoNome"
          v-model="novoNome"
          :maxlength="LIMITES.nomeAmbiente"
          class="w-full max-w-sm rounded-md border border-gray-300 bg-white px-2 py-1 text-sm text-gray-700 outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
          aria-label="Novo nome do ambiente"
          @keydown.enter.prevent="concluirRenomear"
          @keydown.esc="renomeando = false"
          @blur="concluirRenomear"
        />
        <h3 v-else class="flex items-baseline gap-2 text-sm font-semibold text-zinc-900">
          <span class="truncate">{{ ambiente.nome }}</span>
          <span class="shrink-0 text-xs font-normal text-zinc-500">{{ moveis.length }} {{ moveis.length === 1 ? 'móvel' : 'móveis' }}</span>
        </h3>
      </div>
      </div>

      <span v-if="incluiCustos" class="text-sm tabular-nums text-zinc-500 md:text-right">{{ custoAmbiente != null ? formatCurrency(custoAmbiente) : '—' }}</span>
      <span class="text-sm font-semibold tabular-nums text-zinc-900 md:text-right">{{ formatCurrency(ambiente.subtotal_centavos) }}</span>

      <div class="flex items-center justify-end gap-0.5">

      <button
        v-if="editavel"
        type="button"
        class="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold text-brand-primary hover:bg-brand-primary-light cursor-pointer"
        :data-testid="`adicionar-movel-${ambiente.id}`"
        @click="abrirMovel(ambiente.id)"
      >
        <Plus :size="14" /> Móvel
      </button>

      <!-- Menu "⋯" (D20: subir/descer por botões, acessíveis pelo teclado) -->
      <div v-if="editavel" ref="menuRef" class="relative">
        <button
          type="button"
          class="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-200/60 cursor-pointer"
          :aria-label="`Ações do ambiente ${ambiente.nome}`"
          aria-haspopup="menu"
          :aria-expanded="menuAberto"
          @click="menuAberto = !menuAberto"
        >
          <MoreHorizontal :size="16" />
        </button>
        <div v-if="menuAberto" role="menu" class="absolute right-0 z-30 mt-1 w-40 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" @click="comecarRenomear">Renomear</button>
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" :disabled="primeiro" @click="menuAberto = false; emit('subir')">Subir</button>
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" :disabled="ultimo" @click="menuAberto = false; emit('descer')">Descer</button>
          <button type="button" role="menuitem" class="block w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 cursor-pointer" @click="excluirAmbiente">
            Excluir
          </button>
        </div>
      </div>
      </div>
    </div>

    <!-- Os móveis do ambiente -->
    <template v-if="aberto">
      <ul v-if="moveis.length" class="divide-y divide-zinc-100">
        <MovelLinha
          v-for="(movel, indice) in moveis"
          :key="movel.id"
          :movel="movel"
          :editavel="editavel"
          :com-custos="incluiCustos"
          :primeiro="indice === 0"
          :ultimo="indice === moveis.length - 1"
          @editar="abrirMovel(ambiente.id, movel)"
          @duplicar="acoesOrcamento.duplicarMovel(movel.id)"
          @subir="moverMovel(indice, -1)"
          @descer="moverMovel(indice, 1)"
          @excluir="excluirMovel(movel)"
        />
      </ul>
      <p v-else class="px-4 py-3 pl-14 text-sm text-zinc-500">
        Nenhum móvel neste ambiente.
        <button v-if="editavel" type="button" class="font-semibold text-brand-primary hover:underline cursor-pointer" @click="abrirMovel(ambiente.id)">Adicionar o primeiro</button>
      </p>
    </template>
  </div>
</template>
