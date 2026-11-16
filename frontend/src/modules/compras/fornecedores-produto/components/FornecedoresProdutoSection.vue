<script setup lang="ts">
/**
 * @fileoverview Aba Fornecedores do produto (módulo Compras, fase 1).
 *
 * De quem a loja compra este produto: código do fornecedor, em que embalagem
 * compra (fardo de 12...), prazo e último preço pago. O aviso de "mais barato"
 * compara POR UNIDADE — fardo de 12 e caixa de 24 só batem assim (plano, D18).
 *
 * Mesmo desenho da seção de Embalagens: independente do formulário do
 * produto, com o próprio "Salvar" (rota própria, replace-all), e só com o
 * produto já salvo. Quem renderiza (ProductModal) já conferiu módulo e
 * permissão de ver; aqui decide só editar e ver preço.
 *
 * O preço que chega sozinho: toda nota importada por XML grava o último preço
 * pago ao fornecedor dela. O lojista só digita quando ainda não houve nota.
 */
import { computed, ref, watch } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { Plus, Trash2, Save, Store, Star, TrendingDown } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { PRODUTOS_KEY } from '@/shared/constants/entityKeys';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { formatDataPura } from '@/shared/utils/date.utils';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { formatCurrency } from '@/shared/utils/finance';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

import { useAcessoCompras } from '../../shared/composables/useAcessoCompras';
import { comprasKeys } from '../../shared/constants/queryKeys';
import {
  getFornecedoresDoProduto,
  getFornecedoresQueVendem,
  salvarFornecedoresDoProduto,
} from '../../shared/services/compras.service';
import type { FornecedorDoProdutoEscrita, FornecedorDoProdutoRead } from '../../shared/types/compras.types';

const props = defineProps<{
  produto: ProdutoRead | null;
  disabled?: boolean;
}>();

/**
 * O principal mora no cadastro do produto (`fornecedor_id`), e o formulário
 * do produto, aberto ao lado, guarda o valor de quando abriu: sem este aviso,
 * o "Salvar Alterações" do produto desfaria a troca feita aqui.
 */
const emit = defineEmits<{ principalAlterado: [fornecedorId: number] }>();

interface Linha {
  chave: number;
  fornecedor_id: number | null;
  codigo_fornecedor: string;
  /** `null` = compra na unidade do produto. */
  embalagem_id: number | null;
  /** Só editável sem embalagem: com ela, o fator é o do cadastro da embalagem. */
  fator: number | null;
  /** Em reais, como o BaseMoneyInput trabalha. Por UNIDADE DE COMPRA. */
  precoReais: number | undefined;
  prazo_dias: number | null;
  padrao: boolean;
  // Só leitura (vêm do servidor, não do formulário):
  ultima_compra_em: string | null;
  mais_barato: boolean;
  acima_do_menor_bp: number;
}

const toast = useToast();
const queryClient = useQueryClient();
const { podeGerenciar, podeVerCusto } = useAcessoCompras();

const somenteLeitura = computed(() => props.disabled || !podeGerenciar.value);
const produtoId = computed(() => props.produto?.id ?? 0);

let proximaChave = 1;
const linhas = ref<Linha[]>([]);
const salvas = ref('');

const embalagens = computed(() => (props.produto?.embalagens ?? []).filter((e) => e.ativo));

// --- Dados -------------------------------------------------------------------

const { data: fornecedoresDoProduto, isLoading } = useQuery({
  queryKey: computed(() => comprasKeys.fornecedoresDoProduto(produtoId.value)),
  queryFn: () => getFornecedoresDoProduto(produtoId.value),
  enabled: computed(() => produtoId.value > 0),
});

const { data: opcoes } = useQuery({
  queryKey: comprasKeys.fornecedores(),
  queryFn: getFornecedoresQueVendem,
  enabled: computed(() => !somenteLeitura.value),
  staleTime: 60_000,
});

function linhaDe(f: FornecedorDoProdutoRead): Linha {
  return {
    chave: proximaChave++,
    fornecedor_id: f.fornecedor_id,
    codigo_fornecedor: f.codigo_fornecedor ?? '',
    embalagem_id: f.embalagem_id,
    fator: f.fator,
    precoReais: f.ultimo_preco != null ? f.ultimo_preco / 100 : undefined,
    prazo_dias: f.prazo_dias,
    padrao: f.padrao,
    ultima_compra_em: f.ultima_compra_em,
    mais_barato: f.mais_barato,
    acima_do_menor_bp: f.acima_do_menor_bp,
  };
}

function carregar(lista: FornecedorDoProdutoRead[] | undefined) {
  linhas.value = (lista ?? []).map(linhaDe);
  salvas.value = JSON.stringify(payload());
}

watch(fornecedoresDoProduto, (lista) => carregar(lista), { immediate: true });

const alterado = computed(() => JSON.stringify(payload()) !== salvas.value);

/** Nome para exibir, mesmo antes de a lista de opções carregar. */
const nomes = computed(() => {
  const mapa = new Map<number, string>();
  (fornecedoresDoProduto.value ?? []).forEach((f) => mapa.set(f.fornecedor_id, f.fornecedor_nome));
  (opcoes.value ?? []).forEach((f) => mapa.set(f.id, f.nome_fantasia || f.nome));
  return mapa;
});

// --- Edição ------------------------------------------------------------------

function adicionar() {
  linhas.value.push({
    chave: proximaChave++,
    fornecedor_id: null,
    codigo_fornecedor: '',
    embalagem_id: null,
    fator: 1,
    precoReais: undefined,
    prazo_dias: null,
    padrao: linhas.value.length === 0,
    ultima_compra_em: null,
    mais_barato: false,
    acima_do_menor_bp: 0,
  });
}

function remover(chave: number) {
  linhas.value = linhas.value.filter((l) => l.chave !== chave);
}

function marcarPrincipal(chave: number) {
  linhas.value.forEach((l) => (l.padrao = l.chave === chave));
}

function fatorDe(l: Linha): number {
  if (l.embalagem_id != null) {
    return embalagens.value.find((e) => e.id === l.embalagem_id)?.fator ?? 1;
  }
  return Number(l.fator) || 0;
}

function unidadeDeCompra(l: Linha): string {
  const emb = embalagens.value.find((e) => e.id === l.embalagem_id);
  return emb ? emb.sigla : (props.produto?.unidade_medida ?? 'UN');
}

/** "R$ 3,33 a unidade" — só quando compra em mais de uma unidade. */
function precoPorUnidade(l: Linha): string | null {
  const fator = fatorDe(l);
  if (l.precoReais == null || fator <= 1) return null;
  return formatCurrency(Math.round((l.precoReais * 100) / fator));
}

function opcoesPara(l: Linha) {
  const usados = new Set(linhas.value.filter((x) => x.chave !== l.chave).map((x) => x.fornecedor_id));
  return (opcoes.value ?? []).filter((f) => !usados.has(f.id));
}

// --- Salvar ------------------------------------------------------------------

function payload(): FornecedorDoProdutoEscrita[] {
  return linhas.value.map((l) => ({
    fornecedor_id: Number(l.fornecedor_id) || 0,
    codigo_fornecedor: l.codigo_fornecedor.trim() || null,
    embalagem_id: l.embalagem_id,
    fator: fatorDe(l),
    ultimo_preco: l.precoReais != null ? Math.round(l.precoReais * 100) : null,
    prazo_dias: l.prazo_dias != null && (l.prazo_dias as unknown) !== '' ? Number(l.prazo_dias) : null,
    padrao: l.padrao,
  }));
}

const problemas = computed(() => {
  const lista: string[] = [];
  const vistos = new Set<number>();
  linhas.value.forEach((l, i) => {
    const n = `Fornecedor ${i + 1}`;
    if (!l.fornecedor_id) lista.push(`${n}: escolha o fornecedor.`);
    else if (vistos.has(l.fornecedor_id)) lista.push(`${n}: este fornecedor já está na lista.`);
    else vistos.add(l.fornecedor_id);
    if (l.embalagem_id == null && (!l.fator || l.fator < 1 || !Number.isInteger(Number(l.fator)))) {
      lista.push(`${n}: informe quantas unidades vêm em cada compra (1 se compra avulso).`);
    }
    const prazo = l.prazo_dias as unknown;
    if (prazo !== null && prazo !== '' && !(Number(prazo) >= 0 && Number(prazo) <= 365)) {
      lista.push(`${n}: prazo entre 0 e 365 dias.`);
    }
  });
  return lista;
});

const mutation = useMutation<FornecedorDoProdutoRead[], AxiosError<ApiError>, FornecedorDoProdutoEscrita[]>({
  mutationFn: (lista) => salvarFornecedoresDoProduto(produtoId.value, lista),
  onSuccess: (salvasAgora) => {
    const principal = salvasAgora.find((f) => f.padrao)?.fornecedor_id;
    if (principal != null && principal !== props.produto?.fornecedor_id) emit('principalAlterado', principal);
    queryClient.setQueryData(comprasKeys.fornecedoresDoProduto(produtoId.value), salvasAgora);
    carregar(salvasAgora);
    toast.success('Fornecedores salvos');
    // O principal mora no cadastro do produto (`fornecedor_id`).
    queryClient.invalidateQueries({ queryKey: [PRODUTOS_KEY] });
  },
  onError: (erro) => {
    toast.error('Não foi possível salvar os fornecedores', getErrorMessage(erro, 'Confira os dados e tente de novo.') as string);
  },
});

function salvar() {
  if (!props.produto || problemas.value.length) return;
  mutation.mutate(payload());
}

function percentual(bp: number): string {
  return `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}
</script>

<template>
  <div class="space-y-4">
    <p class="text-xs text-zinc-500">
      De quem a loja compra este produto. O <strong>último preço</strong> se atualiza sozinho a cada nota
      importada por XML; o fornecedor <strong>principal</strong> é o do cadastro do produto.
    </p>

    <div
      v-if="!produto"
      class="flex items-start gap-2 p-3 rounded-xl bg-zinc-50 border border-zinc-200 text-xs text-zinc-600"
    >
      <Store :size="15" class="shrink-0 mt-0.5" />
      Salve o produto primeiro; depois, ao editá-lo, os fornecedores aparecem aqui.
    </div>

    <p v-else-if="isLoading" class="text-sm text-zinc-400 text-center py-4">Carregando fornecedores…</p>

    <template v-else>
      <div
        v-for="(l, i) in linhas"
        :key="l.chave"
        class="rounded-xl border p-4 space-y-3"
        :class="l.padrao ? 'border-brand-primary/30 bg-brand-primary/5' : 'border-zinc-200'"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Fornecedor {{ i + 1 }}</span>
            <span
              v-if="l.padrao"
              class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-primary/10 text-brand-primary border border-brand-primary/20"
            >
              <Star :size="10" /> Principal
            </span>
            <span
              v-if="podeVerCusto && l.mais_barato"
              class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200"
              title="Menor preço por unidade entre os fornecedores com preço"
            >
              <TrendingDown :size="10" /> Mais barato
            </span>
            <span
              v-else-if="podeVerCusto && l.acima_do_menor_bp > 0"
              class="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200"
              title="Quanto o preço por unidade está acima do fornecedor mais barato"
            >
              {{ percentual(l.acima_do_menor_bp) }} mais caro
            </span>
          </div>
          <div v-if="!somenteLeitura" class="flex items-center gap-1">
            <button
              v-if="!l.padrao"
              type="button"
              class="px-2 py-1 rounded-lg text-xs text-zinc-500 hover:text-brand-primary hover:bg-brand-primary/5 cursor-pointer"
              @click="marcarPrincipal(l.chave)"
            >
              Tornar principal
            </button>
            <!-- O principal é o do cadastro do produto: para trocá-lo, torne outro principal. -->
            <button
              v-if="!l.padrao"
              type="button"
              class="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
              title="Tirar este fornecedor do produto"
              @click="remover(l.chave)"
            >
              <Trash2 :size="15" />
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-12 gap-3">
          <label class="campo col-span-2 md:col-span-5">
            <span>Fornecedor</span>
            <select v-model.number="l.fornecedor_id" :disabled="somenteLeitura">
              <option :value="null" disabled>Escolha…</option>
              <!-- A opção atual sempre existe, mesmo antes de a lista carregar. -->
              <option v-if="l.fornecedor_id && !opcoesPara(l).some((f) => f.id === l.fornecedor_id)" :value="l.fornecedor_id">
                {{ nomes.get(l.fornecedor_id) ?? `Fornecedor ${l.fornecedor_id}` }}
              </option>
              <option v-for="f in opcoesPara(l)" :key="f.id" :value="f.id">{{ f.nome_fantasia || f.nome }}</option>
            </select>
          </label>
          <label class="campo col-span-2 md:col-span-3">
            <span>Código no fornecedor</span>
            <input v-model="l.codigo_fornecedor" :disabled="somenteLeitura" maxlength="60" placeholder="opcional" />
          </label>
          <label class="campo md:col-span-2">
            <span>Compra em</span>
            <select v-model="l.embalagem_id" :disabled="somenteLeitura">
              <option :value="null">{{ produto?.unidade_medida ?? 'UN' }} (avulso)</option>
              <option v-for="e in embalagens" :key="e.id" :value="e.id">{{ e.sigla }} com {{ e.fator }}</option>
            </select>
          </label>
          <label class="campo md:col-span-2" title="Unidades do produto em cada compra">
            <span>Unidades</span>
            <input
              v-if="l.embalagem_id == null"
              v-model.number="l.fator"
              :disabled="somenteLeitura"
              type="number"
              min="1"
              step="1"
            />
            <input v-else :value="fatorDe(l)" disabled />
          </label>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
          <div v-if="podeVerCusto" class="md:col-span-3">
            <BaseMoneyInput v-model="l.precoReais" :label="`Último preço (${unidadeDeCompra(l)})`" :disabled="somenteLeitura" />
          </div>
          <label class="campo md:col-span-2">
            <span>Prazo (dias)</span>
            <input v-model.number="l.prazo_dias" :disabled="somenteLeitura" type="number" min="0" max="365" placeholder="—" />
          </label>
          <p class="md:col-span-7 text-xs text-zinc-500 pb-2.5">
            <template v-if="podeVerCusto && precoPorUnidade(l)">
              {{ precoPorUnidade(l) }} a unidade.
            </template>
            <template v-if="l.ultima_compra_em">
              Última compra em {{ formatDataPura(l.ultima_compra_em) }}.
            </template>
          </p>
        </div>
      </div>

      <p v-if="!linhas.length" class="text-sm text-zinc-400 text-center py-4 border border-dashed border-zinc-200 rounded-xl">
        Nenhum fornecedor ainda. Eles também aparecem sozinhos ao importar a nota de compra por XML.
      </p>

      <ul v-if="problemas.length && !somenteLeitura" class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-1">
        <li v-for="p in problemas" :key="p">{{ p }}</li>
      </ul>

      <div v-if="!somenteLeitura" class="flex flex-wrap justify-between gap-2">
        <BaseButton type="button" variant="ghost" class="flex items-center gap-2" @click="adicionar">
          <Plus :size="16" />
          Adicionar fornecedor
        </BaseButton>
        <BaseButton
          type="button"
          class="flex items-center gap-2"
          :disabled="!alterado || problemas.length > 0"
          :is-loading="mutation.isPending.value"
          @click="salvar"
        >
          <Save :size="16" />
          Salvar fornecedores
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
