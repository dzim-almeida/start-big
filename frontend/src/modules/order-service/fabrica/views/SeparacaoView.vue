<script setup lang="ts">
/**
 * @fileoverview Separação de material da OS da fábrica (docs/marcenaria-fabrica-plano.md, F4).
 *
 * O almoxarife bipa cada chapa, rolo e ferragem que sai para a produção — no
 * PC com leitor ou no celular, na rede da loja. A BAIXA no estoque acontece
 * no bipe (o fechamento da OS só baixa o que não foi separado).
 *
 * Sem preço nenhum: é a tela de quem confere quantidade (DC5). O campo do
 * leitor fica sempre focado; sem leitor, cada linha tem "+1" e "Separar tudo".
 */
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { ArrowLeft, CheckCircle2, MapPin, ScanLine, Undo2 } from 'lucide-vue-next';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import MotivoModal from '@/modules/compras/shared/components/MotivoModal.vue';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';

import { fabricaKeys } from '../constants/queryKeys';
import { estornarSeparacao, getSeparacao, separar } from '../services/fabrica.service';
import type { ItemSeparacao, SeparacaoRead } from '../types/fabrica.types';

const route = useRoute();
const router = useRouter();
const toast = useToast();
const queryClient = useQueryClient();

const numeroOs = computed(() => String(route.params.numeroOs ?? ''));

const { data, isLoading, isError } = useQuery({
  queryKey: computed(() => fabricaKeys.separacao(numeroOs.value)),
  queryFn: () => getSeparacao(numeroOs.value),
  enabled: computed(() => !!numeroOs.value),
});

const separados = computed(() => data.value?.itens.filter((i) => i.falta <= 0).length ?? 0);
const total = computed(() => data.value?.itens.length ?? 0);

// --- Leitor --------------------------------------------------------------------

const codigo = ref('');
const leitor = ref<HTMLInputElement | null>(null);
const ultimo = ref<string | null>(null);

function focar() {
  nextTick(() => leitor.value?.focus());
}
onMounted(focar);

function aoGravar(novo: SeparacaoRead) {
  queryClient.setQueryData(fabricaKeys.separacao(numeroOs.value), novo);
  // O trilho e a OS mudam (trava da etapa, reserva, estoque).
  queryClient.invalidateQueries({ queryKey: fabricaKeys.trilho(numeroOs.value) });
}

const bipe = useMutation<SeparacaoRead, AxiosError<ApiError>, { codigo?: string; itemId?: number; quantidade?: number }>({
  mutationFn: (alvo) => separar(numeroOs.value, alvo, alvo.quantidade ?? 1),
  onSuccess: (novo, alvo) => {
    aoGravar(novo);
    const item = alvo.itemId
      ? novo.itens.find((i) => i.item_id === alvo.itemId)
      : novo.itens.find((i) => i.codigos.includes(alvo.codigo ?? ''));
    ultimo.value = item ? `${item.descricao}: ${item.separada} de ${item.quantidade}` : null;
    if (novo.completa) toast.success('Tudo separado', 'A OS já pode seguir para a produção.');
  },
  onError: (erro) => toast.error('Não separou', getErrorMessage(erro, 'Confira o código.') as string),
  onSettled: () => {
    codigo.value = '';
    focar();
  },
});

function aoLer() {
  const lido = codigo.value.trim();
  if (lido) bipe.mutate({ codigo: lido });
}

function separarTudo(item: ItemSeparacao) {
  bipe.mutate({ itemId: item.item_id, quantidade: item.falta });
}

// --- Estorno -------------------------------------------------------------------

const estornando = ref<ItemSeparacao | null>(null);
const estorno = useMutation<SeparacaoRead, AxiosError<ApiError>, string>({
  mutationFn: (motivo) =>
    estornarSeparacao(numeroOs.value, estornando.value!.item_id, estornando.value!.separada, motivo),
  onSuccess: (novo) => {
    estornando.value = null;
    aoGravar(novo);
    toast.success('Devolvido ao estoque');
    focar();
  },
  onError: (erro) => toast.error('Não foi possível estornar', getErrorMessage(erro, 'Tente de novo.') as string),
});

function quantidade(n: number): string {
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 3 });
}
</script>

<template>
  <div class="flex flex-col gap-5 max-w-3xl">
    <div class="flex items-center gap-3">
      <button type="button" class="p-2 rounded-lg text-zinc-500 hover:bg-zinc-100 cursor-pointer" title="Voltar" @click="router.back()">
        <ArrowLeft :size="18" />
      </button>
      <PageReview
        :title="`Separação · ${numeroOs}`"
        :description="[data?.cliente, data?.projeto].filter(Boolean).join(' — ') || 'Material da OS'"
      />
    </div>

    <p v-if="isLoading" class="py-8 text-center text-sm text-zinc-400">Carregando…</p>
    <p v-else-if="isError" class="text-sm text-rose-600">Não foi possível abrir a separação desta OS.</p>

    <template v-else-if="data">
      <p v-if="!data.pode_separar" class="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">
        A separação começa na etapa "Separação e compra", depois do sinal.
      </p>

      <!-- Leitor -->
      <form v-if="data.pode_separar" class="flex items-center gap-2 rounded-2xl border-2 border-brand-primary/40 bg-white px-3" @submit.prevent="aoLer">
        <ScanLine :size="20" class="text-brand-primary shrink-0" />
        <input
          ref="leitor"
          v-model="codigo"
          type="text"
          inputmode="text"
          autocomplete="off"
          class="w-full min-h-14 text-lg bg-transparent outline-none"
          placeholder="Bipe o código da chapa, do rolo ou da ferragem"
          :disabled="bipe.isPending.value"
        />
      </form>
      <p v-if="ultimo" class="text-sm text-emerald-700 -mt-2">✓ {{ ultimo }}</p>

      <!-- Progresso -->
      <div class="flex items-center gap-3">
        <div class="flex-1 h-2 rounded-full bg-zinc-100 overflow-hidden">
          <div class="h-full bg-emerald-500 transition-all" :style="{ width: `${total ? (separados / total) * 100 : 0}%` }" />
        </div>
        <span class="text-sm font-bold tabular-nums text-zinc-700">{{ separados }} de {{ total }}</span>
        <CheckCircle2 v-if="data.completa" :size="18" class="text-emerald-600" />
      </div>

      <!-- Itens -->
      <ul class="space-y-2">
        <li
          v-for="item in data.itens"
          :key="item.item_id"
          class="rounded-xl border bg-white p-3 flex flex-wrap items-center gap-3"
          :class="item.falta <= 0 ? 'border-emerald-200 bg-emerald-50/40' : 'border-zinc-200'"
        >
          <div class="flex-1 min-w-48">
            <p class="font-semibold text-zinc-800">{{ item.descricao }}</p>
            <p class="text-xs text-zinc-500 flex flex-wrap gap-x-3">
              <span v-if="item.localizacao" class="inline-flex items-center gap-1"><MapPin :size="11" /> {{ item.localizacao }}</span>
              <span>Estoque: {{ quantidade(item.saldo_estoque) }} {{ item.unidade }}</span>
            </p>
          </div>
          <p class="text-lg font-black tabular-nums" :class="item.falta <= 0 ? 'text-emerald-700' : 'text-zinc-800'">
            {{ quantidade(item.separada) }} / {{ quantidade(item.quantidade) }}
            <span class="text-xs font-semibold text-zinc-500">{{ item.unidade }}</span>
          </p>
          <div v-if="data.pode_separar" class="flex items-center gap-1">
            <BaseButton
              v-if="item.falta > 0"
              type="button" size="sm" variant="secondary"
              :disabled="bipe.isPending.value"
              @click="bipe.mutate({ itemId: item.item_id })"
            >
              +1
            </BaseButton>
            <BaseButton
              v-if="item.falta > 1"
              type="button" size="sm" variant="ghost"
              :disabled="bipe.isPending.value"
              @click="separarTudo(item)"
            >
              Separar tudo
            </BaseButton>
            <button
              v-if="item.separada > 0"
              type="button"
              class="p-2 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
              title="Devolver ao estoque o que foi separado"
              @click="estornando = item"
            >
              <Undo2 :size="16" />
            </button>
          </div>
        </li>
      </ul>
      <p v-if="!data.itens.length" class="text-sm text-zinc-500 text-center py-6">
        Esta OS não tem material do estoque para separar.
      </p>
    </template>

    <MotivoModal
      :aberto="!!estornando"
      :titulo="`Devolver ${estornando?.descricao ?? ''} ao estoque`"
      :descricao="`O que foi separado (${estornando ? quantidade(estornando.separada) : ''}) volta para a prateleira e para a reserva da OS.`"
      confirm-label="Devolver"
      placeholder="Ex.: chapa com defeito, separei a errada"
      :carregando="estorno.isPending.value"
      @fechar="estornando = null"
      @confirmar="estorno.mutate($event)"
    />
  </div>
</template>
