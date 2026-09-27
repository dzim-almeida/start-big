<script setup lang="ts">
/**
 * @fileoverview Embalagens do produto: fardo, caixa, pack (plano de embalagens, fase 1).
 *
 * Componente INDEPENDENTE do formulário do produto, com o próprio "Salvar":
 * o PUT das embalagens é replace-all numa rota própria, e amarrar isso ao
 * submit do produto misturaria duas transações. Por isso também só aparece
 * com o produto já salvo (a embalagem precisa do id dele).
 *
 * O estoque NÃO muda aqui: continua na unidade do produto. A embalagem é só
 * uma forma de vender e de receber — com código de barras e preço próprios.
 */
import { computed, ref, watch } from 'vue';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { Plus, Trash2, Package, Save } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import type { ApiError } from '@/shared/types/axios.types';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { formatCurrency } from '@/shared/utils/finance';
import { precoDaEmbalagem, precoUnitarioNaEmbalagem } from '@/shared/utils/embalagem';
import { resolverCodigo, nomeSimbologia } from '@/shared/etiquetas/codigoBarras';
import { PRODUTOS_QUERY_KEY } from '../../../shared/constants/queryKeys';
import { salvarEmbalagens } from '../../services/embalagem.service';
import type { EmbalagemEscrita, EmbalagemRead } from '../../types/embalagens.types';
import type { ProdutoRead } from '../../types/products.types';

const props = defineProps<{
  produto: ProdutoRead | null;
  disabled?: boolean;
}>();

type ModoPreco = 'proprio' | 'desconto' | 'soma';

interface Linha {
  chave: number;
  id?: number;
  sigla: string;
  descricao: string;
  fator: number | null;
  codigo_barras: string;
  gerar_codigo_interno: boolean;
  modoPreco: ModoPreco;
  /** Em reais, como o BaseMoneyInput trabalha. */
  precoReais: number | undefined;
  descontoPct: number | null;
  vende_no_pdv: boolean;
  usa_na_entrada: boolean;
  ativo: boolean;
}

const SIGLAS_SUGERIDAS = ['FD', 'CX', 'PCT', 'DP', 'UN'];

const toast = useToast();
const queryClient = useQueryClient();

let proximaChave = 1;
const linhas = ref<Linha[]>([]);
const salvas = ref<string>('');
/** A3: recusar a unidade avulsa no caixa (distribuidora que não abre fardo). */
const soFechada = ref(false);

function linhaDe(e: EmbalagemRead): Linha {
  return {
    chave: proximaChave++,
    id: e.id,
    sigla: e.sigla,
    descricao: e.descricao ?? '',
    fator: e.fator,
    codigo_barras: e.codigo_barras ?? '',
    gerar_codigo_interno: false,
    modoPreco: e.preco != null ? 'proprio' : e.desconto_bp != null ? 'desconto' : 'soma',
    precoReais: e.preco != null ? e.preco / 100 : undefined,
    descontoPct: e.desconto_bp != null ? e.desconto_bp / 100 : null,
    vende_no_pdv: e.vende_no_pdv,
    usa_na_entrada: e.usa_na_entrada,
    ativo: e.ativo,
  };
}

function carregar(embalagens: EmbalagemRead[] | undefined, fechada: boolean) {
  linhas.value = (embalagens ?? []).map(linhaDe);
  soFechada.value = fechada;
  salvas.value = retrato();
}

/** O que conta como "alterado": as linhas e a opção de só vender fechado. */
function retrato(): string {
  return JSON.stringify([payload(), soFechada.value]);
}

watch(
  () => props.produto?.id,
  () => carregar(props.produto?.embalagens, !!props.produto?.so_embalagem_fechada),
  { immediate: true },
);

const precoUnidade = computed(() => props.produto?.estoque.valor_varejo ?? 0);
const alterado = computed(() => retrato() !== salvas.value);

function adicionar() {
  const ja = new Set(linhas.value.map((l) => l.sigla));
  linhas.value.push({
    chave: proximaChave++,
    sigla: ja.has('FD') ? 'CX' : 'FD',
    descricao: '',
    fator: null,
    codigo_barras: '',
    gerar_codigo_interno: false,
    modoPreco: 'proprio',
    precoReais: undefined,
    descontoPct: null,
    vende_no_pdv: true,
    usa_na_entrada: true,
    ativo: true,
  });
}

function remover(chave: number) {
  linhas.value = linhas.value.filter((l) => l.chave !== chave);
}

// --- Leitura para a tela ------------------------------------------------------

function precoCalculado(l: Linha): { total: number; unidade: number } | null {
  if (!l.fator || l.fator < 1) return null;
  const emb = {
    fator: l.fator,
    preco: l.modoPreco === 'proprio' && l.precoReais != null ? Math.round(l.precoReais * 100) : null,
    desconto_bp: l.modoPreco === 'desconto' && l.descontoPct != null ? Math.round(l.descontoPct * 100) : null,
  };
  return { total: precoDaEmbalagem(emb, precoUnidade.value), unidade: precoUnitarioNaEmbalagem(emb, precoUnidade.value) };
}

/** Como o código sai no leitor/etiqueta — o mesmo selo da Central de Etiquetas. */
function situacaoCodigo(l: Linha): { rotulo: string; classe: string } | null {
  const codigo = l.codigo_barras.trim();
  if (!codigo) {
    return l.gerar_codigo_interno
      ? { rotulo: 'Código interno ao salvar', classe: 'bg-zinc-100 text-zinc-600 border border-zinc-200' }
      : { rotulo: 'Sem código', classe: 'bg-amber-50 text-amber-700 border border-amber-200' };
  }
  const r = resolverCodigo(codigo);
  if (!r) return null;
  if (r.simbologia === 'CODE128') return { rotulo: 'Não é EAN/DUN', classe: 'bg-amber-50 text-amber-700 border border-amber-200' };
  if (codigo.startsWith('29') && r.simbologia === 'EAN13') {
    return { rotulo: 'Código interno', classe: 'bg-zinc-100 text-zinc-600 border border-zinc-200' };
  }
  return { rotulo: nomeSimbologia(r.simbologia), classe: 'bg-emerald-50 text-emerald-700 border border-emerald-200' };
}

// --- Salvar ---------------------------------------------------------------------

function payload(): EmbalagemEscrita[] {
  return linhas.value.map((l) => ({
    ...(l.id != null ? { id: l.id } : {}),
    sigla: l.sigla.trim().toUpperCase(),
    descricao: l.descricao.trim() || null,
    fator: Number(l.fator) || 0,
    codigo_barras: l.codigo_barras.trim() || null,
    preco: l.modoPreco === 'proprio' && l.precoReais != null ? Math.round(l.precoReais * 100) : null,
    desconto_bp: l.modoPreco === 'desconto' && l.descontoPct != null ? Math.round(l.descontoPct * 100) : null,
    vende_no_pdv: l.vende_no_pdv,
    usa_na_entrada: l.usa_na_entrada,
    ativo: l.ativo,
    gerar_codigo_interno: l.gerar_codigo_interno && !l.codigo_barras.trim(),
  }));
}

const problemas = computed(() => {
  const lista: string[] = [];
  linhas.value.forEach((l, i) => {
    const n = `Embalagem ${i + 1}`;
    if (!/^[A-Za-z0-9]{1,6}$/.test(l.sigla.trim())) lista.push(`${n}: sigla de 1 a 6 letras ou números (ex.: FD).`);
    if (!l.fator || l.fator < 1 || !Number.isInteger(Number(l.fator))) lista.push(`${n}: informe quantas unidades ela tem.`);
    if (l.modoPreco === 'proprio' && l.precoReais == null) lista.push(`${n}: informe o preço, ou escolha "soma das unidades".`);
    if (l.modoPreco === 'desconto' && (l.descontoPct == null || l.descontoPct < 0 || l.descontoPct > 99)) {
      lista.push(`${n}: desconto entre 0 e 99%.`);
    }
  });
  return lista;
});

const mutation = useMutation<EmbalagemRead[], AxiosError<ApiError>, EmbalagemEscrita[]>({
  mutationFn: (lista) => salvarEmbalagens(props.produto!.id, lista, soFechada.value),
  onSuccess: (salvasAgora) => {
    carregar(salvasAgora, soFechada.value);
    toast.success('Embalagens salvas');
    queryClient.invalidateQueries({ queryKey: [PRODUTOS_QUERY_KEY] });
  },
  onError: (erro) => {
    toast.error('Não foi possível salvar as embalagens', getErrorMessage(erro, 'Confira os códigos e tente de novo.') as string);
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
      Venda e receba em <strong>fardo, caixa ou pack</strong> sem criar outro produto. O estoque continua contado em
      unidade: vender 1 fardo de 12 baixa 12 unidades. Quantidade 1 serve de <strong>código de barras extra</strong> da
      própria unidade.
    </p>

    <div
      v-if="!produto"
      class="flex items-start gap-2 p-3 rounded-xl bg-zinc-50 border border-zinc-200 text-xs text-zinc-600"
    >
      <Package :size="15" class="shrink-0 mt-0.5" />
      Salve o produto primeiro; depois, ao editá-lo, as embalagens aparecem aqui.
    </div>

    <template v-else>
      <div
        v-for="(l, i) in linhas"
        :key="l.chave"
        class="rounded-xl border border-zinc-200 p-4 space-y-3"
        :class="!l.ativo && 'opacity-60'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Embalagem {{ i + 1 }}</span>
          <button
            v-if="!disabled"
            type="button"
            class="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
            title="Remover embalagem"
            @click="remover(l.chave)"
          >
            <Trash2 :size="15" />
          </button>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-12 gap-3">
          <label class="campo md:col-span-2">
            <span>Sigla</span>
            <input v-model="l.sigla" :disabled="disabled" list="siglas-embalagem" maxlength="6" placeholder="FD" />
          </label>
          <label class="campo md:col-span-2">
            <span>Quantidade (un)</span>
            <input v-model.number="l.fator" :disabled="disabled" type="number" min="1" step="1" placeholder="12" />
          </label>
          <label class="campo col-span-2 md:col-span-4">
            <span>Descrição (caixa e etiqueta)</span>
            <input v-model="l.descricao" :disabled="disabled" maxlength="60" :placeholder="`Fardo com ${l.fator || 12}`" />
          </label>
          <label class="campo col-span-2 md:col-span-4">
            <span class="flex items-center justify-between gap-2">
              Código de barras
              <span v-if="situacaoCodigo(l)" :class="['px-1.5 py-0.5 rounded-full text-[9px] font-bold', situacaoCodigo(l)!.classe]">
                {{ situacaoCodigo(l)!.rotulo }}
              </span>
            </span>
            <input v-model="l.codigo_barras" :disabled="disabled" maxlength="20" placeholder="DUN-14 do fornecedor" />
          </label>
        </div>

        <label v-if="!l.codigo_barras.trim() && !disabled" class="flex items-center gap-2 text-xs text-zinc-600 cursor-pointer select-none">
          <input v-model="l.gerar_codigo_interno" type="checkbox" class="accent-brand-primary" />
          Sem código do fornecedor: gerar um código interno (a etiqueta sai pela Central de Etiquetas)
        </label>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
          <label class="campo md:col-span-4">
            <span>Preço</span>
            <select v-model="l.modoPreco" :disabled="disabled">
              <option value="proprio">Preço próprio</option>
              <option value="desconto">Desconto sobre as unidades</option>
              <option value="soma">Soma das unidades</option>
            </select>
          </label>
          <div v-if="l.modoPreco === 'proprio'" class="md:col-span-3">
            <BaseMoneyInput v-model="l.precoReais" label="Preço da embalagem" :disabled="disabled" />
          </div>
          <label v-else-if="l.modoPreco === 'desconto'" class="campo md:col-span-3">
            <span>Desconto (%)</span>
            <input v-model.number="l.descontoPct" :disabled="disabled" type="number" min="0" max="99" step="0.5" placeholder="5" />
          </label>
          <div v-else class="md:col-span-3" />
          <p v-if="precoCalculado(l)" class="md:col-span-5 text-xs text-zinc-500 pb-2.5">
            Sai por <strong class="text-zinc-800">{{ formatCurrency(precoCalculado(l)!.total) }}</strong>
            — {{ formatCurrency(precoCalculado(l)!.unidade) }} a unidade
            <template v-if="precoUnidade">(avulsa: {{ formatCurrency(precoUnidade) }})</template>
          </p>
        </div>

        <div class="flex flex-wrap gap-x-5 gap-y-2 text-xs text-zinc-600">
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input v-model="l.vende_no_pdv" :disabled="disabled" type="checkbox" class="accent-brand-primary" />
            Vende no caixa
          </label>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input v-model="l.usa_na_entrada" :disabled="disabled" type="checkbox" class="accent-brand-primary" />
            Usa na entrada de estoque
          </label>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input v-model="l.ativo" :disabled="disabled" type="checkbox" class="accent-brand-primary" />
            Ativa
          </label>
        </div>
      </div>

      <datalist id="siglas-embalagem">
        <option v-for="s in SIGLAS_SUGERIDAS" :key="s" :value="s" />
      </datalist>

      <p v-if="!linhas.length" class="text-sm text-zinc-400 text-center py-4 border border-dashed border-zinc-200 rounded-xl">
        Nenhuma embalagem. Este produto só é vendido em unidade.
      </p>

      <label
        v-if="linhas.some((l) => Number(l.fator) > 1)"
        class="flex items-start gap-2 text-xs text-zinc-600 cursor-pointer select-none"
      >
        <input v-model="soFechada" :disabled="disabled" type="checkbox" class="accent-brand-primary mt-0.5" />
        <span>
          <strong>Só vende em embalagem fechada</strong> — o caixa recusa a unidade avulsa deste produto
          (para quem não abre fardo).
        </span>
      </label>

      <ul v-if="problemas.length && !disabled" class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-1">
        <li v-for="p in problemas" :key="p">{{ p }}</li>
      </ul>

      <div v-if="!disabled" class="flex flex-wrap justify-between gap-2">
        <BaseButton type="button" variant="ghost" class="flex items-center gap-2" @click="adicionar">
          <Plus :size="16" />
          Adicionar embalagem
        </BaseButton>
        <BaseButton
          type="button"
          class="flex items-center gap-2"
          :disabled="!alterado || problemas.length > 0"
          :is-loading="mutation.isPending.value"
          @click="salvar"
        >
          <Save :size="16" />
          Salvar embalagens
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
.campo input,
.campo select {
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
.campo input:focus,
.campo select:focus {
  border-color: var(--color-brand-primary);
}
.campo input:disabled,
.campo select:disabled {
  background: #f4f4f5;
  color: #71717a;
}
</style>
