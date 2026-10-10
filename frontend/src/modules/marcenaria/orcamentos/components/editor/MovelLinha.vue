<script setup lang="ts">
/**
 * @component MovelLinha
 * @description Um móvel na tabela "Ambientes e móveis" do editor (Spec 06B
 * §6.2; redesign 10/2026): nome e descrição, medidas, quantidade, produção,
 * custo (só com custos) e preço. "Editar" fica à vista; duplicar, subir,
 * descer e excluir ficam no menu "⋯", para a linha não virar uma fileira de ícones.
 *
 * Nenhum número é calculado aqui (C8): preço e custo vêm prontos da API.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { MoreHorizontal, Pencil } from 'lucide-vue-next';

import BaseStatusPill from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import { formatCurrency } from '@/shared/utils/finance';

import type { MovelDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { formatarMedidas } from '../../utils/conversoes';
import { gradeMoveis } from './gradeMoveis';

const props = defineProps<{
  movel: MovelDetalhe;
  editavel: boolean;
  /** Quem vê custos tem a coluna "Custo" (06A D23). */
  comCustos: boolean;
  primeiro: boolean;
  ultimo: boolean;
}>();

const emit = defineEmits<{
  editar: [];
  duplicar: [];
  subir: [];
  descer: [];
  excluir: [];
}>();

const medidas = computed(() =>
  formatarMedidas(props.movel.largura_mm, props.movel.altura_mm, props.movel.profundidade_mm),
);

/** Custo total do móvel: só existe na resposta de quem vê custos (06A D23). */
const custoTotal = computed(() => {
  const calculo = props.movel.calculo;
  return calculo && 'custo_total_centavos' in calculo ? calculo.custo_total_centavos : null;
});

const terceirizado = computed(() => props.movel.tipo_producao === 'TERCEIRIZADA');

const menuAberto = ref(false);
const menuRef = ref<HTMLElement | null>(null);
onClickOutside(menuRef, () => { menuAberto.value = false; });

function escolher(acao: 'duplicar' | 'subir' | 'descer' | 'excluir') {
  menuAberto.value = false;
  if (acao === 'duplicar') emit('duplicar');
  else if (acao === 'subir') emit('subir');
  else if (acao === 'descer') emit('descer');
  else emit('excluir');
}

const CLASSE_ITEM_MENU = 'block w-full px-3 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 disabled:opacity-40 cursor-pointer';
</script>

<template>
  <!-- Não aprovado (08B D13): fica como histórico, esmaecido e com selo. -->
  <li
    :class="[
      'flex flex-col gap-1.5 px-4 py-3 md:items-center',
      gradeMoveis(comCustos),
      movel.aprovado === false ? 'opacity-50' : '',
    ]"
    :data-testid="`movel-${movel.id}`"
  >
    <!-- Móvel (o recuo do nome fica aqui dentro: a grade é a mesma do cabeçalho) -->
    <div class="min-w-0 pl-2 md:pl-10">
      <p class="flex items-center gap-2 text-sm font-medium text-zinc-900">
        <span class="truncate">{{ movel.nome }}</span>
        <BaseStatusPill v-if="movel.aprovado === false" tom="neutro" data-testid="selo-nao-aprovado">Não aprovado</BaseStatusPill>
      </p>
      <p v-if="movel.descricao" class="truncate text-xs text-zinc-500">{{ movel.descricao }}</p>
    </div>

    <p class="text-sm tabular-nums whitespace-nowrap text-zinc-600">{{ medidas || '—' }}</p>
    <p class="text-sm tabular-nums text-zinc-600 md:text-right">{{ movel.quantidade }}</p>

    <div class="min-w-0">
      <BaseStatusPill :tom="terceirizado ? 'info' : 'sucesso'">
        <span class="truncate">{{ terceirizado ? `Terceirizado${movel.central ? ` · ${movel.central.nome}` : ''}` : 'Interna' }}</span>
      </BaseStatusPill>
    </div>

    <p v-if="comCustos" class="text-sm tabular-nums text-zinc-500 md:text-right" data-testid="custo-movel">
      {{ custoTotal != null ? formatCurrency(custoTotal) : '—' }}
    </p>
    <p class="text-sm font-semibold tabular-nums text-zinc-900 md:text-right">
      {{ movel.calculo ? formatCurrency(movel.calculo.preco_total_centavos) : '—' }}
    </p>

    <!-- Ações só no rascunho (acoes.editar, D13). Editar vira "Ver" fora dele. -->
    <div class="flex items-center justify-end gap-0.5">
      <button
        type="button"
        class="rounded-md p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 cursor-pointer"
        :aria-label="editavel ? `Editar ${movel.nome}` : `Ver ${movel.nome}`"
        @click="emit('editar')"
      >
        <Pencil :size="15" />
      </button>
      <div v-if="editavel" ref="menuRef" class="relative">
        <button
          type="button"
          class="rounded-md p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 cursor-pointer"
          :aria-label="`Mais ações de ${movel.nome}`"
          aria-haspopup="menu"
          :aria-expanded="menuAberto"
          @click="menuAberto = !menuAberto"
        >
          <MoreHorizontal :size="15" />
        </button>
        <div v-if="menuAberto" role="menu" class="absolute right-0 z-30 mt-1 w-40 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" :aria-label="`Duplicar ${movel.nome}`" @click="escolher('duplicar')">Duplicar</button>
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" :disabled="primeiro" :aria-label="`Subir ${movel.nome}`" @click="escolher('subir')">Subir</button>
          <button type="button" role="menuitem" :class="CLASSE_ITEM_MENU" :disabled="ultimo" :aria-label="`Descer ${movel.nome}`" @click="escolher('descer')">Descer</button>
          <button
            type="button"
            role="menuitem"
            class="block w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 cursor-pointer"
            :aria-label="`Excluir ${movel.nome}`"
            @click="escolher('excluir')"
          >
            Excluir
          </button>
        </div>
      </div>
    </div>
  </li>
</template>
