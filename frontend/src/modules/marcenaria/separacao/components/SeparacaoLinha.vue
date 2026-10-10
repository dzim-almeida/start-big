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
import { Check, MapPin, MoreHorizontal } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseStatusPill, { type TomStatus } from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';

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
const ALERTAS: Record<string, { texto: string; tom: TomStatus }> = {
  [ALERTAS_SEPARACAO.semCobertura]: { texto: 'Falta no estoque', tom: 'alerta' },
  [ALERTAS_SEPARACAO.estoqueNegativo]: { texto: 'Estoque negativo: conferir a contagem', tom: 'perigo' },
  [ALERTAS_SEPARACAO.acimaDoSugerido]: { texto: 'Retirado acima do sugerido', tom: 'neutro' },
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
  <!-- Uma linha da tabela de separação (redesign 10/2026). As colunas batem com o cabeçalho de OSSeparacaoTab. -->
  <div
    :id="`separacao-linha-${linha.item_id}`"
    class="grid grid-cols-1 items-center gap-x-4 gap-y-2 px-5 py-3.5 transition-colors md:grid-cols-[minmax(0,2fr)_minmax(0,1.6fr)_minmax(0,1fr)_minmax(0,1fr)_auto]"
    :class="[
      linha.concluida ? 'bg-zinc-50/70' : alertas.some((a) => a.tom === 'perigo') ? 'bg-red-50/40' : 'bg-white',
      destacada ? 'ring-2 ring-inset ring-brand-primary/60' : '',
    ]"
    :data-testid="`linha-${linha.item_id}`"
  >
    <!-- Insumo e os móveis que usam (D5 da 10A): "Balcão 2,2" -->
    <div class="min-w-0">
      <p class="text-sm font-semibold text-zinc-900" :class="linha.concluida ? 'text-zinc-500' : ''">
        {{ linha.descricao }}
        <span v-if="linha.codigo" class="ml-1 text-xs font-normal text-zinc-500">{{ linha.codigo }}</span>
      </p>
      <p v-if="linha.moveis.length" class="mt-1 flex flex-wrap gap-1">
        <span v-for="(movel, i) in linha.moveis" :key="i" class="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
          {{ movel.nome }} {{ quantidadeSimples(movel.planejado_milesimos) }}
        </span>
      </p>
    </div>

    <!-- Quantidades: concluída vira um resumo só (D7); aberta mostra os três números (D3) -->
    <p v-if="linha.nao_usado" class="text-sm text-zinc-500" data-testid="linha-nao-usado">Não usado</p>
    <p v-else-if="linha.concluida" class="inline-flex items-center gap-1 text-sm font-medium text-emerald-700" data-testid="linha-concluida">
      <Check :size="16" /> Retirado {{ q(linha.separada_milesimos) }}
    </p>
    <dl v-else class="grid grid-cols-3 gap-3">
      <div>
        <dt class="text-xs text-zinc-500">Sugerido</dt>
        <dd class="text-sm font-bold tabular-nums text-zinc-900" data-testid="sugerido">{{ q(sugerido) }}</dd>
      </div>
      <div>
        <dt class="text-xs text-zinc-500">Retirado</dt>
        <dd class="text-sm font-bold tabular-nums text-zinc-900" data-testid="retirado">{{ q(linha.separada_milesimos) }}</dd>
      </div>
      <div>
        <dt class="text-xs text-zinc-500">No estoque</dt>
        <dd
          class="text-sm font-bold tabular-nums"
          :class="linha.no_estoque_milesimos < linha.falta_milesimos ? 'text-amber-700' : 'text-zinc-900'"
          data-testid="no-estoque"
        >
          {{ q(linha.no_estoque_milesimos) }}
        </dd>
      </div>
    </dl>

    <!-- Localização: a lista está na ordem das prateleiras -->
    <div>
      <span
        class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium"
        :class="linha.localizacao ? 'bg-brand-primary-light text-brand-primary' : 'bg-zinc-100 text-zinc-500'"
      >
        <MapPin :size="13" aria-hidden="true" />
        {{ linha.localizacao || 'Sem localização' }}
      </span>
    </div>

    <!-- Situação e avisos (D8) -->
    <div class="flex min-w-0 flex-wrap gap-1.5">
      <BaseStatusPill v-for="alerta in alertas" :key="alerta.texto" :tom="alerta.tom" quebra-linha>{{ alerta.texto }}</BaseStatusPill>
      <BaseStatusPill v-if="!alertas.length && linha.concluida && !linha.nao_usado" tom="sucesso">Separado</BaseStatusPill>
      <BaseStatusPill v-else-if="!alertas.length && !linha.concluida" tom="neutro">Pendente</BaseStatusPill>
    </div>

    <!-- Ações: Retirar em destaque; o resto no menu (D3) -->
    <div v-if="editavel" class="flex shrink-0 items-center justify-end gap-2">
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
    <div v-else />
  </div>
</template>
