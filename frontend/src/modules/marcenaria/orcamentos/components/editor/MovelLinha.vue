<script setup lang="ts">
/**
 * @component MovelLinha
 * @description Um móvel dentro do cartão do ambiente (Spec 06B §6.2):
 * nome, medidas, quantidade, produção, preço e as ações (editar, duplicar,
 * subir, descer, excluir). Com custos, o custo aparece em cinza abaixo do preço.
 *
 * Nenhum número é calculado aqui (C8): preço e custo vêm prontos da API.
 */
import { computed } from 'vue';
import { ArrowDown, ArrowUp, Copy, Pencil, Trash2 } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';

import type { MovelDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { formatarMedidas } from '../../utils/conversoes';

const props = defineProps<{
  movel: MovelDetalhe;
  editavel: boolean;
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

/** Classe dos botõezinhos de ação (iguais em todos). */
const CLASSE_ACAO =
  'rounded-md p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 disabled:cursor-not-allowed disabled:opacity-30 cursor-pointer';
</script>

<template>
  <!-- Não aprovado (08B D13): fica como histórico, esmaecido e com selo. -->
  <li
    class="flex flex-wrap items-start justify-between gap-3 py-3"
    :class="movel.aprovado === false ? 'opacity-50' : ''"
    :data-testid="`movel-${movel.id}`"
  >
    <div class="min-w-0 flex-1">
      <p class="flex items-center gap-2 truncate text-sm font-semibold text-zinc-800">
        {{ movel.nome }}
        <span v-if="movel.aprovado === false" class="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-semibold text-zinc-600" data-testid="selo-nao-aprovado">
          Não aprovado
        </span>
      </p>
      <p class="mt-0.5 flex flex-wrap gap-x-3 text-xs text-zinc-500">
        <span v-if="medidas">{{ medidas }}</span>
        <span>{{ movel.quantidade }}×</span>
        <span v-if="movel.tipo_producao === 'TERCEIRIZADA'" class="font-medium text-indigo-700">
          Terceirizada{{ movel.central ? ` · ${movel.central.nome}` : '' }}
        </span>
      </p>
      <p v-if="movel.descricao" class="mt-0.5 truncate text-xs text-zinc-400">{{ movel.descricao }}</p>
    </div>

    <div class="flex items-center gap-3">
      <div class="text-right">
        <p class="text-sm font-semibold tabular-nums text-zinc-800">
          {{ movel.calculo ? formatCurrency(movel.calculo.preco_total_centavos) : '—' }}
        </p>
        <p v-if="custoTotal != null" class="text-[11px] tabular-nums text-zinc-400" data-testid="custo-movel">
          custo {{ formatCurrency(custoTotal) }}
        </p>
      </div>

      <!-- Ações só no rascunho (acoes.editar, D13). Editar vira "Ver" fora dele. -->
      <div class="flex items-center">
        <button type="button" :class="CLASSE_ACAO" :aria-label="editavel ? `Editar ${movel.nome}` : `Ver ${movel.nome}`" @click="emit('editar')">
          <Pencil :size="15" />
        </button>
        <template v-if="editavel">
          <button type="button" :class="CLASSE_ACAO" :aria-label="`Duplicar ${movel.nome}`" @click="emit('duplicar')">
            <Copy :size="15" />
          </button>
          <button type="button" :class="CLASSE_ACAO" :disabled="primeiro" :aria-label="`Subir ${movel.nome}`" @click="emit('subir')">
            <ArrowUp :size="15" />
          </button>
          <button type="button" :class="CLASSE_ACAO" :disabled="ultimo" :aria-label="`Descer ${movel.nome}`" @click="emit('descer')">
            <ArrowDown :size="15" />
          </button>
          <button
            type="button"
            class="rounded-md p-1.5 text-zinc-400 hover:bg-red-50 hover:text-red-600 cursor-pointer"
            :aria-label="`Excluir ${movel.nome}`"
            @click="emit('excluir')"
          >
            <Trash2 :size="15" />
          </button>
        </template>
      </div>
    </div>
  </li>
</template>
