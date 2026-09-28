<script setup lang="ts">
/**
 * @fileoverview Preço por quantidade do produto: faixas "a partir de N" (R2) e
 * "leve X, pague Y" (R3) — plano de embalagens, §6.1 (fase 5).
 *
 * Mesmo desenho da EmbalagensSection: componente INDEPENDENTE do formulário,
 * com o próprio "Salvar" (PUT replace-all numa rota própria), fora do <form> e
 * só com o produto já salvo.
 *
 * O cadastro vale só com a chave da regra ligada em Regras de Vendas; a tela
 * mostra cada bloco apenas quando a chave dele está ligada.
 */
import { computed, ref, watch } from 'vue';
import { useMutation, useQuery } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { Plus, Trash2, Save, Tags } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import type { ApiError } from '@/shared/types/axios.types';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { formatCurrency } from '@/shared/utils/finance';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';
import { getRegrasPreco, salvarRegrasPreco } from '../../services/regraPreco.service';
import type { RegraPrecoEscrita, RegraPrecoRead, TipoRegraPreco } from '../../types/regrasPreco.types';
import type { ProdutoRead } from '../../types/products.types';

const props = defineProps<{
  produto: ProdutoRead | null;
  disabled?: boolean;
}>();

interface Linha {
  chave: number;
  id?: number;
  tipo: TipoRegraPreco;
  quantidade: number | null;
  /** Em reais, como o BaseMoneyInput trabalha. */
  precoReais: number | undefined;
  pague: number | null;
  inicio: string;
  fim: string;
  ativo: boolean;
}

const toast = useToast();
const configStore = useConfiguracoesStore();

let proximaChave = 1;
const linhas = ref<Linha[]>([]);
const salvas = ref('');

const produtoId = computed(() => props.produto?.id ?? null);
const precoUnidade = computed(() => props.produto?.estoque.valor_varejo ?? 0);

const { data: regras } = useQuery({
  queryKey: computed(() => ['produto-regras-preco', produtoId.value]),
  queryFn: () => getRegrasPreco(produtoId.value!),
  enabled: computed(() => produtoId.value != null),
});

function linhaDe(r: RegraPrecoRead): Linha {
  return {
    chave: proximaChave++,
    id: r.id,
    tipo: r.tipo,
    quantidade: r.quantidade,
    precoReais: r.preco != null ? r.preco / 100 : undefined,
    pague: r.pague,
    inicio: r.inicio ?? '',
    fim: r.fim ?? '',
    ativo: r.ativo,
  };
}

function carregar(lista: RegraPrecoRead[] | undefined) {
  linhas.value = (lista ?? []).map(linhaDe);
  salvas.value = JSON.stringify(payload());
}

watch(regras, (lista) => carregar(lista), { immediate: true });

const alterado = computed(() => JSON.stringify(payload()) !== salvas.value);
const faixas = computed(() => linhas.value.filter((l) => l.tipo === 'FAIXA'));
const promocoes = computed(() => linhas.value.filter((l) => l.tipo === 'LEVE_PAGUE'));

function adicionar(tipo: TipoRegraPreco) {
  linhas.value.push({
    chave: proximaChave++,
    tipo,
    quantidade: tipo === 'FAIXA' ? 6 : 3,
    precoReais: undefined,
    pague: tipo === 'LEVE_PAGUE' ? 2 : null,
    inicio: '',
    fim: '',
    ativo: true,
  });
}

function remover(chave: number) {
  linhas.value = linhas.value.filter((l) => l.chave !== chave);
}

/** O que a regra faz, em reais, para o dono conferir antes de salvar. */
function exemplo(l: Linha): string | null {
  const n = Number(l.quantidade);
  if (!n || n < 2 || !precoUnidade.value) return null;
  if (l.tipo === 'FAIXA') {
    if (l.precoReais == null) return null;
    const preco = Math.round(l.precoReais * 100);
    if (preco >= precoUnidade.value) return 'O preço da faixa precisa ser menor que o da unidade.';
    return `${n} un saem por ${formatCurrency(n * preco)} em vez de ${formatCurrency(n * precoUnidade.value)}`;
  }
  const y = Number(l.pague);
  if (!y || y >= n) return null;
  return `${n} un saem por ${formatCurrency(y * precoUnidade.value)} em vez de ${formatCurrency(n * precoUnidade.value)}`;
}

function payload(): RegraPrecoEscrita[] {
  return linhas.value.map((l) => ({
    ...(l.id != null ? { id: l.id } : {}),
    tipo: l.tipo,
    quantidade: Number(l.quantidade) || 0,
    preco: l.tipo === 'FAIXA' && l.precoReais != null ? Math.round(l.precoReais * 100) : null,
    pague: l.tipo === 'LEVE_PAGUE' ? Number(l.pague) || null : null,
    inicio: l.inicio || null,
    fim: l.fim || null,
    ativo: l.ativo,
  }));
}

const problemas = computed(() => {
  const lista: string[] = [];
  const vistas = new Set<number>();
  linhas.value.forEach((l) => {
    const n = Number(l.quantidade);
    const nome = l.tipo === 'FAIXA' ? `Faixa "a partir de ${n || '?'}"` : `Leve ${n || '?'}, pague ${l.pague || '?'}`;
    if (!Number.isInteger(n) || n < 2) lista.push(`${nome}: a quantidade precisa ser 2 ou mais.`);
    if (l.tipo === 'FAIXA') {
      if (l.precoReais == null) lista.push(`${nome}: informe o preço da unidade.`);
      if (l.ativo && vistas.has(n)) lista.push(`${nome}: há duas faixas com a mesma quantidade.`);
      vistas.add(n);
    } else if (!l.pague || l.pague < 1 || l.pague >= n) {
      lista.push(`${nome}: "pague" precisa ser menor que "leve".`);
    }
    if (l.inicio && l.fim && l.inicio > l.fim) lista.push(`${nome}: o início é depois do fim.`);
  });
  return lista;
});

const mutation = useMutation<RegraPrecoRead[], AxiosError<ApiError>, RegraPrecoEscrita[]>({
  mutationFn: (lista) => salvarRegrasPreco(props.produto!.id, lista),
  onSuccess: (salvasAgora) => {
    carregar(salvasAgora);
    toast.success('Preços por quantidade salvos');
  },
  onError: (erro) => {
    toast.error('Não foi possível salvar', getErrorMessage(erro, 'Confira as faixas e tente de novo.') as string);
  },
});

function salvar() {
  if (!props.produto || problemas.value.length) return;
  mutation.mutate(payload());
}
</script>

<template>
  <div class="space-y-4">
    <p class="text-xs text-zinc-500">
      O caixa aplica sozinho, e a linha da venda mostra a regra usada. Quando mais de uma serve, vale o que está em
      <strong>Configurações › Regras de Vendas</strong>.
    </p>

    <div
      v-if="!produto"
      class="flex items-start gap-2 p-3 rounded-xl bg-zinc-50 border border-zinc-200 text-xs text-zinc-600"
    >
      <Tags :size="15" class="shrink-0 mt-0.5" />
      Salve o produto primeiro; depois, ao editá-lo, os preços por quantidade aparecem aqui.
    </div>

    <template v-else>
      <!-- R2 -->
      <div v-if="configStore.regraFaixasQuantidade" class="space-y-2">
        <p class="text-xs font-bold uppercase tracking-wider text-zinc-500">A partir de N unidades</p>
        <div
          v-for="l in faixas"
          :key="l.chave"
          class="grid grid-cols-2 md:grid-cols-12 gap-3 items-end rounded-xl border border-zinc-200 p-3"
          :class="!l.ativo && 'opacity-60'"
        >
          <label class="campo md:col-span-2">
            <span>A partir de (un)</span>
            <input v-model.number="l.quantidade" :disabled="disabled" type="number" min="2" step="1" />
          </label>
          <div class="md:col-span-3">
            <BaseMoneyInput v-model="l.precoReais" label="Cada unidade sai por" :disabled="disabled" />
          </div>
          <label class="campo md:col-span-2">
            <span>Início</span>
            <input v-model="l.inicio" :disabled="disabled" type="date" />
          </label>
          <label class="campo md:col-span-2">
            <span>Fim</span>
            <input v-model="l.fim" :disabled="disabled" type="date" />
          </label>
          <div class="col-span-2 md:col-span-3 flex items-center justify-between gap-2 pb-2">
            <label class="flex items-center gap-2 text-xs text-zinc-600 cursor-pointer select-none">
              <input v-model="l.ativo" :disabled="disabled" type="checkbox" class="accent-brand-primary" />
              Ativa
            </label>
            <button
              v-if="!disabled"
              type="button"
              class="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
              title="Remover faixa"
              @click="remover(l.chave)"
            >
              <Trash2 :size="15" />
            </button>
          </div>
          <p v-if="exemplo(l)" class="col-span-2 md:col-span-12 text-xs text-zinc-500 -mt-1">{{ exemplo(l) }}</p>
        </div>
        <BaseButton v-if="!disabled" type="button" variant="ghost" class="flex items-center gap-2" @click="adicionar('FAIXA')">
          <Plus :size="16" />
          Adicionar faixa
        </BaseButton>
      </div>

      <!-- R3 -->
      <div v-if="configStore.regraLevePague" class="space-y-2">
        <p class="text-xs font-bold uppercase tracking-wider text-zinc-500">Leve X, pague Y</p>
        <div
          v-for="l in promocoes"
          :key="l.chave"
          class="grid grid-cols-2 md:grid-cols-12 gap-3 items-end rounded-xl border border-zinc-200 p-3"
          :class="!l.ativo && 'opacity-60'"
        >
          <label class="campo md:col-span-2">
            <span>Leve</span>
            <input v-model.number="l.quantidade" :disabled="disabled" type="number" min="2" step="1" />
          </label>
          <label class="campo md:col-span-3">
            <span>Pague</span>
            <input v-model.number="l.pague" :disabled="disabled" type="number" min="1" step="1" />
          </label>
          <label class="campo md:col-span-2">
            <span>Início</span>
            <input v-model="l.inicio" :disabled="disabled" type="date" />
          </label>
          <label class="campo md:col-span-2">
            <span>Fim</span>
            <input v-model="l.fim" :disabled="disabled" type="date" />
          </label>
          <div class="col-span-2 md:col-span-3 flex items-center justify-between gap-2 pb-2">
            <label class="flex items-center gap-2 text-xs text-zinc-600 cursor-pointer select-none">
              <input v-model="l.ativo" :disabled="disabled" type="checkbox" class="accent-brand-primary" />
              Ativa
            </label>
            <button
              v-if="!disabled"
              type="button"
              class="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
              title="Remover promoção"
              @click="remover(l.chave)"
            >
              <Trash2 :size="15" />
            </button>
          </div>
          <p v-if="exemplo(l)" class="col-span-2 md:col-span-12 text-xs text-zinc-500 -mt-1">{{ exemplo(l) }}</p>
        </div>
        <BaseButton v-if="!disabled" type="button" variant="ghost" class="flex items-center gap-2" @click="adicionar('LEVE_PAGUE')">
          <Plus :size="16" />
          Adicionar promoção
        </BaseButton>
      </div>

      <ul v-if="problemas.length && !disabled" class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-1">
        <li v-for="p in problemas" :key="p">{{ p }}</li>
      </ul>

      <div v-if="!disabled" class="flex justify-end">
        <BaseButton
          type="button"
          class="flex items-center gap-2"
          :disabled="!alterado || problemas.length > 0"
          :is-loading="mutation.isPending.value"
          @click="salvar"
        >
          <Save :size="16" />
          Salvar preços por quantidade
        </BaseButton>
      </div>
    </template>
  </div>
</template>

<style scoped>
.campo {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}
.campo > span {
  font-size: 0.75rem;
  font-weight: 500;
  color: #374151;
}
.campo input {
  width: 100%;
  min-width: 0;
  min-height: 2.5rem;
  padding: 0.5rem 0.625rem;
  font-size: 0.875rem;
  border: 1px solid #e4e4e7;
  border-radius: 0.5rem;
  background: #fff;
  outline: none;
}
.campo input:focus {
  border-color: var(--color-brand-primary);
}
.campo input:disabled {
  background: #f4f4f5;
  color: #71717a;
}
</style>
