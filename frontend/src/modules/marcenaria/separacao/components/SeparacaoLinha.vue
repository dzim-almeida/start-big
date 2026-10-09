<script setup lang="ts">
/**
 * @component SeparacaoLinha
 * @description Uma linha da separação (Spec 10B D3, D7, D8).
 *
 * A localização vem primeiro (a lista está na ordem do depósito), depois o
 * nome e três números grandes: Sugerido, Retirado e "No estoque p/ esta OS"
 * (a conta do Compras na fila das OS abertas). Abaixo, os móveis que usam.
 * Nenhum preço (D9). Linha concluída ou não usada fica esmaecida.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { Check, MoreHorizontal } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { ALERTAS_SEPARACAO, type LinhaSeparacao } from '../schemas/separacao.schema';
import { quantidadeComUnidade, quantidadeSimples } from '../utils/quantidades';

const props = defineProps<{
  linha: LinhaSeparacao;
  /** A OS ainda aceita mudanças (D10). */
  editavel: boolean;
  /** Acabou de ser lida pelo leitor: destaque por 2 s (D14). */
  destacada?: boolean;
}>();

const emit = defineEmits<{
  retirar: [];
  devolver: [];
  concluir: [];
  naoUsado: [];
  reabrir: [];
}>();

const menuAberto = ref(false);
const menuRef = ref<HTMLElement | null>(null);
onClickOutside(menuRef, () => { menuAberto.value = false; });

const q = (milesimos: number) => quantidadeComUnidade(milesimos, props.linha.unidade);

/** O "sugerido" do orçamento; sem ele (produto mudou de unidade), o que a OS consome. */
const sugerido = computed(() => props.linha.sugerido_milesimos ?? props.linha.quantidade_milesimos);

/** Os avisos da linha, em frase (D8). Código desconhecido não aparece. */
const ALERTAS: Record<string, { texto: string; classe: string }> = {
  [ALERTAS_SEPARACAO.semCobertura]: { texto: 'Falta no estoque', classe: 'bg-amber-50 text-amber-800 border-amber-200' },
  [ALERTAS_SEPARACAO.estoqueNegativo]: {
    texto: 'Estoque negativo: conferir a contagem', classe: 'bg-red-50 text-red-700 border-red-200',
  },
  [ALERTAS_SEPARACAO.acimaDoSugerido]: { texto: 'Retirado acima do sugerido', classe: 'bg-zinc-100 text-zinc-600 border-zinc-200' },
};
const alertas = computed(() => props.linha.alertas.map((codigo) => ALERTAS[codigo]).filter(Boolean));

/** O menu "⋯" só oferece o que faz sentido agora (e nada com a OS fechada). */
const opcoes = computed(() => {
  const { concluida, nao_usado: naoUsado, separada_milesimos: separada } = props.linha;
  const lista: { id: 'devolver' | 'concluir' | 'naoUsado' | 'reabrir'; texto: string }[] = [];
  if (separada > 0) lista.push({ id: 'devolver', texto: 'Devolver ao estoque' });
  if (!concluida && separada > 0) lista.push({ id: 'concluir', texto: 'Concluir (usou menos)' });
  if (!concluida && separada === 0) lista.push({ id: 'naoUsado', texto: 'Não usado nesta OS' });
  if (concluida || naoUsado) lista.push({ id: 'reabrir', texto: 'Reabrir' });
  return lista;
});

function escolher(id: 'devolver' | 'concluir' | 'naoUsado' | 'reabrir') {
  menuAberto.value = false;
  if (id === 'devolver') emit('devolver');
  else if (id === 'concluir') emit('concluir');
  else if (id === 'naoUsado') emit('naoUsado');
  else emit('reabrir');
}
</script>

<template>
  <div
    :id="`separacao-linha-${linha.item_id}`"
    class="flex flex-wrap items-start gap-x-4 gap-y-2 rounded-xl border px-4 py-3 transition-colors"
    :class="[
      linha.concluida ? 'border-zinc-100 bg-zinc-50 opacity-70' : 'border-zinc-200 bg-white',
      destacada ? 'ring-2 ring-brand-primary/60' : '',
    ]"
    :data-testid="`linha-${linha.item_id}`"
  >
    <!-- Localização primeiro: a lista está na ordem das prateleiras -->
    <p class="w-36 shrink-0 pt-1 text-xs font-bold uppercase tracking-wide text-zinc-500">
      {{ linha.localizacao || 'Sem localização' }}
    </p>

    <div class="min-w-0 flex-1">
      <p class="text-sm font-semibold text-zinc-900">
        {{ linha.descricao }}
        <span v-if="linha.codigo" class="ml-1 text-xs font-normal text-zinc-400">{{ linha.codigo }}</span>
      </p>

      <!-- Concluída: um resumo só (D7) -->
      <p v-if="linha.nao_usado" class="mt-1 inline-flex items-center gap-1 text-sm text-zinc-500" data-testid="linha-nao-usado">
        Não usado
      </p>
      <p v-else-if="linha.concluida" class="mt-1 inline-flex items-center gap-1 text-sm text-emerald-700" data-testid="linha-concluida">
        <Check :size="16" /> Retirado {{ q(linha.separada_milesimos) }}
      </p>

      <!-- Os três números grandes (D3) -->
      <dl v-else class="mt-1 flex flex-wrap gap-x-6 gap-y-1">
        <div>
          <dt class="text-[11px] text-zinc-500">Sugerido</dt>
          <dd class="text-lg font-bold tabular-nums text-zinc-900" data-testid="sugerido">{{ q(sugerido) }}</dd>
        </div>
        <div>
          <dt class="text-[11px] text-zinc-500">Retirado</dt>
          <dd class="text-lg font-bold tabular-nums text-zinc-900" data-testid="retirado">{{ q(linha.separada_milesimos) }}</dd>
        </div>
        <div>
          <dt class="text-[11px] text-zinc-500">No estoque p/ esta OS</dt>
          <dd
            class="text-lg font-bold tabular-nums"
            :class="linha.no_estoque_milesimos < linha.falta_milesimos ? 'text-amber-700' : 'text-zinc-900'"
            data-testid="no-estoque"
          >
            {{ q(linha.no_estoque_milesimos) }}
          </dd>
        </div>
      </dl>

      <!-- Os móveis que usam (D5 da 10A): "Balcão 2,2" -->
      <p v-if="linha.moveis.length" class="mt-1 text-xs text-zinc-500">
        <span v-for="(movel, i) in linha.moveis" :key="i">
          {{ movel.nome }} {{ quantidadeSimples(movel.planejado_milesimos) }}<template v-if="i < linha.moveis.length - 1"> · </template>
        </span>
      </p>

      <!-- Avisos (D8) -->
      <div v-if="alertas.length" class="mt-2 flex flex-wrap gap-1.5">
        <span v-for="alerta in alertas" :key="alerta.texto" class="rounded-full border px-2 py-0.5 text-[11px]" :class="alerta.classe">
          {{ alerta.texto }}
        </span>
      </div>
    </div>

    <!-- Ações: Retirar em destaque; o resto no menu (D3) -->
    <div v-if="editavel" class="flex shrink-0 items-center gap-2">
      <BaseButton v-if="!linha.concluida" size="sm" data-testid="acao-retirar" @click="emit('retirar')">Retirar</BaseButton>
      <div v-if="opcoes.length" ref="menuRef" class="relative">
        <BaseButton variant="secondary" size="sm" aria-haspopup="menu" :aria-expanded="menuAberto" aria-label="Mais ações" data-testid="menu-linha" @click="menuAberto = !menuAberto">
          <MoreHorizontal :size="16" />
        </BaseButton>
        <div v-if="menuAberto" role="menu" class="absolute right-0 z-30 mt-1 w-52 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
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
    </div>
  </div>
</template>
