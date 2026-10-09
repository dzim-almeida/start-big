<script setup lang="ts">
/**
 * @component AmbienteCard
 * @description Um ambiente do orçamento (Spec 06B D19, D20, §6.2): cartão
 * recolhível com o subtotal BRUTO (antes do desconto, como na proposta), os
 * móveis e o menu "⋯" (renomear, subir, descer, excluir).
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

const props = defineProps<{
  ambiente: AmbienteDetalhe;
  primeiro: boolean;
  ultimo: boolean;
}>();

const emit = defineEmits<{ subir: []; descer: [] }>();

const { editavel, acoesOrcamento, confirmar, abrirMovel } = useEditor();

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
  <article class="rounded-xl border border-zinc-200" :data-testid="`ambiente-${ambiente.id}`">
    <header class="flex items-center gap-2 px-4 py-3">
      <button
        type="button"
        class="rounded p-1 text-zinc-400 hover:bg-zinc-100 cursor-pointer"
        :aria-expanded="aberto"
        :aria-label="aberto ? `Recolher ${ambiente.nome}` : `Abrir ${ambiente.nome}`"
        @click="aberto = !aberto"
      >
        <ChevronDown :size="16" class="transition-transform" :class="aberto ? '' : '-rotate-90'" />
      </button>

      <input
        v-if="renomeando"
        ref="campoNome"
        v-model="novoNome"
        :maxlength="LIMITES.nomeAmbiente"
        class="flex-1 rounded-md border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        aria-label="Novo nome do ambiente"
        @keydown.enter.prevent="concluirRenomear"
        @keydown.esc="renomeando = false"
        @blur="concluirRenomear"
      />
      <h3 v-else class="flex-1 truncate text-sm font-bold text-zinc-800">{{ ambiente.nome }}</h3>

      <span class="text-xs text-zinc-500">Subtotal</span>
      <span class="text-sm font-semibold tabular-nums text-zinc-800">{{ formatCurrency(ambiente.subtotal_centavos) }}</span>

      <!-- Menu "⋯" (D20: subir/descer por botões, acessíveis pelo teclado) -->
      <div v-if="editavel" ref="menuRef" class="relative">
        <button
          type="button"
          class="rounded p-1 text-zinc-400 hover:bg-zinc-100 cursor-pointer"
          :aria-label="`Ações do ambiente ${ambiente.nome}`"
          aria-haspopup="menu"
          :aria-expanded="menuAberto"
          @click="menuAberto = !menuAberto"
        >
          <MoreHorizontal :size="16" />
        </button>
        <div v-if="menuAberto" role="menu" class="absolute right-0 z-20 mt-1 w-40 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" @click="comecarRenomear">Renomear</button>
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" :disabled="primeiro" @click="menuAberto = false; emit('subir')">Subir</button>
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" :disabled="ultimo" @click="menuAberto = false; emit('descer')">Descer</button>
          <button type="button" role="menuitem" class="block w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 cursor-pointer" @click="excluirAmbiente">
            Excluir
          </button>
        </div>
      </div>
    </header>

    <div v-if="aberto" class="border-t border-zinc-100 px-4">
      <ul v-if="moveis.length" class="divide-y divide-zinc-100">
        <MovelLinha
          v-for="(movel, indice) in moveis"
          :key="movel.id"
          :movel="movel"
          :editavel="editavel"
          :primeiro="indice === 0"
          :ultimo="indice === moveis.length - 1"
          @editar="abrirMovel(ambiente.id, movel)"
          @duplicar="acoesOrcamento.duplicarMovel(movel.id)"
          @subir="moverMovel(indice, -1)"
          @descer="moverMovel(indice, 1)"
          @excluir="excluirMovel(movel)"
        />
      </ul>
      <p v-else class="py-3 text-xs text-zinc-400">Nenhum móvel neste ambiente.</p>

      <button
        v-if="editavel"
        type="button"
        class="my-3 inline-flex items-center gap-1 text-sm font-medium text-brand-primary hover:underline cursor-pointer"
        :data-testid="`adicionar-movel-${ambiente.id}`"
        @click="abrirMovel(ambiente.id)"
      >
        <Plus :size="14" /> Adicionar móvel
      </button>
    </div>
  </article>
</template>
