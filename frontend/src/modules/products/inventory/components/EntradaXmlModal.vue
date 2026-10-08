<script setup lang="ts">
/**
 * Entrada de mercadoria pela XML da NF-e do fornecedor.
 *
 * Três passos: escolher o arquivo → conferir item a item → resumo. Nada é
 * gravado antes do "Dar entrada": a prévia só lê. Quantidade e custo vêm da
 * nota (o servidor relê o XML); aqui o lojista decide QUAL produto cada item
 * é, se entra por caixa/fardo e se cadastra o que não existe.
 * Ver backend-fastapi/docs/entrada-xml-nfe-plano.md.
 */
import { computed, reactive, ref, watch } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { FileUp, CheckCircle2, AlertTriangle, Link2, PackagePlus, Ban, Tag } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';
import { formatCurrency } from '@/shared/utils/finance';
import { PRODUTOS_QUERY_KEY } from '@/modules/products/shared/constants/queryKeys';
import { MOVIMENTACOES_QUERY_KEY } from '../composables/useMovimentacoesQuery';
import { importarNotaXml, lerNotaXml } from '../services/nfeEntrada.service';
import type { ItemPrevia, NotaPrevia, ResultadoImportacao } from '../types/nfeEntrada.types';
import type { ProdutoRead } from '../types/products.types';

const props = defineProps<{ isOpen: boolean; produtos: ProdutoRead[] }>();
const emit = defineEmits<{
  close: [];
  /** Manda o que entrou para a fila de etiquetas: [produto_id, unidades]. */
  etiquetas: [entradas: { produto_id: number; unidades: number }[]];
}>();

const toast = useToast();
const queryClient = useQueryClient();

type Acao = 'vincular' | 'criar' | 'ignorar';
interface Linha {
  acao: Acao;
  produtoId: string;
  embalagemId: string;
  fator: number;
  nome: string;
  codigo: string;
  codigoBarras: string;
  precoReais: number | undefined;
  /** "É 1 mesmo" — só existe para item em CX/FD sem o fator dito. */
  fatorConfirmado: boolean;
}

const etapa = ref<'arquivo' | 'conferencia' | 'pronto'>('arquivo');
const xml = ref('');
const previa = ref<NotaPrevia | null>(null);
const linhas = reactive<Record<number, Linha>>({});
const lancarContas = ref(false);
const lendo = ref(false);
const importando = ref(false);
const resultado = ref<ResultadoImportacao | null>(null);
const arrastando = ref(false);

watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  etapa.value = 'arquivo';
  xml.value = '';
  previa.value = null;
  resultado.value = null;
  for (const k of Object.keys(linhas)) delete linhas[Number(k)];
});

// ── Passo 1: arquivo ─────────────────────────────────────────────────────────

async function lerArquivo(arquivo: File | undefined) {
  if (!arquivo) return;
  lendo.value = true;
  try {
    xml.value = await arquivo.text();
    const lida = await lerNotaXml(xml.value);
    previa.value = lida;
    for (const item of lida.itens) linhas[item.indice] = linhaInicial(item);
    lancarContas.value = lida.financeiro_disponivel && lida.duplicatas.length > 0;
    etapa.value = 'conferencia';
  } catch (erro) {
    toast.error('Não foi possível ler a nota', getErrorMessage(erro as AxiosError<ApiError>, 'Confira se o arquivo é o XML da NF-e.'));
  } finally {
    lendo.value = false;
  }
}

function aoEscolher(evento: Event) {
  const input = evento.target as HTMLInputElement;
  lerArquivo(input.files?.[0]);
  input.value = '';
}

function aoSoltar(evento: DragEvent) {
  arrastando.value = false;
  lerArquivo(evento.dataTransfer?.files?.[0]);
}

function linhaInicial(item: ItemPrevia): Linha {
  return {
    acao: item.produto ? 'vincular' : 'criar',
    produtoId: item.produto ? String(item.produto.id) : '',
    embalagemId: item.embalagem_id ? String(item.embalagem_id) : '',
    fator: item.fator,
    nome: item.descricao,
    // O código da UNIDADE (cEANTrib) é o que o leitor do caixa vai bipar.
    codigo: item.ean_tributavel ?? item.ean ?? item.codigo,
    codigoBarras: item.ean_tributavel ?? (item.fator === 1 ? (item.ean ?? '') : ''),
    precoReais: undefined,
    fatorConfirmado: false,
  };
}

// ── Passo 2: conferência ─────────────────────────────────────────────────────

const produtoOptions = computed<SelectOption[]>(() =>
  props.produtos.filter((p) => p.ativo).map((p) => ({ value: String(p.id), label: p.nome })),
);

function produtoDe(linha: Linha): ProdutoRead | undefined {
  return props.produtos.find((p) => String(p.id) === linha.produtoId);
}

function embalagemOptions(linha: Linha): SelectOption[] {
  const embalagens = (produtoDe(linha)?.embalagens ?? []).filter((e) => e.ativo && e.fator >= 2);
  return [
    { value: '', label: 'Unidade (informar o fator)' },
    ...embalagens.map((e) => ({ value: String(e.id), label: `${e.sigla} de ${e.fator}` })),
  ];
}

function aoTrocarProduto(linha: Linha, item: ItemPrevia) {
  linha.embalagemId = '';
  linha.fator = item.fator_da_nota;
  linha.fatorConfirmado = false;
}

function aoTrocarEmbalagem(linha: Linha, item: ItemPrevia) {
  const embalagem = produtoDe(linha)?.embalagens?.find((e) => String(e.id) === linha.embalagemId);
  linha.fator = embalagem ? embalagem.fator : item.fator_da_nota;
}

function unidades(item: ItemPrevia): number {
  return item.quantidade * Math.max(1, linhas[item.indice]?.fator || 1);
}

function custoUnidade(item: ItemPrevia): number {
  const u = unidades(item);
  return u > 0 ? Math.round(item.custo_total / u) : 0;
}

function custoAnterior(item: ItemPrevia): number | null {
  const linha = linhas[item.indice];
  if (linha?.acao !== 'vincular') return null;
  const estoque = produtoDe(linha)?.estoque;
  return estoque?.custo_medio ?? estoque?.valor_entrada ?? null;
}

/**
 * "2 CX" que entraria como 2 unidades. Mesma regra do servidor: a unidade da
 * nota é de embalagem, o fator ficou 1 e ninguém disse nada — nem a embalagem
 * do cadastro, nem um vínculo já confirmado, nem o lojista agora.
 */
function fatorPendente(item: ItemPrevia): boolean {
  const l = linhas[item.indice];
  if (!l || l.acao === 'ignorar' || !item.unidade_de_embalagem) return false;
  if (Number(l.fator) !== 1 || l.embalagemId || l.fatorConfirmado) return false;
  const mesmoVinculo = item.reconhecido_por === 'vinculo' && l.acao === 'vincular'
    && l.produtoId === String(item.produto?.id);
  return !mesmoVinculo;
}

function confirmarFatorUm(item: ItemPrevia) {
  linhas[item.indice].fatorConfirmado = true;
}

/**
 * Custo muito diferente do atual é o sinal mais comum de fator errado (12×
 * mais caro = a caixa entrou como unidade) ou de reajuste que merece um olhar.
 * Só avisa: quem decide é o lojista.
 */
function divergenciaCusto(item: ItemPrevia): { pct: number; anterior: number } | null {
  const anterior = custoAnterior(item);
  const novo = custoUnidade(item);
  if (!anterior || anterior <= 0 || !novo) return null;
  const pct = Math.round(((novo - anterior) / anterior) * 100);
  return Math.abs(pct) >= 50 ? { pct, anterior } : null;
}

function problemaDa(item: ItemPrevia): string | null {
  const l = linhas[item.indice];
  if (!l) return null;
  if (fatorPendente(item)) return `Informe quantas unidades vêm em cada ${item.unidade}`;
  if (l.acao === 'vincular' && !l.produtoId) return 'Escolha o produto';
  if (l.acao === 'criar') {
    if (!l.nome.trim()) return 'Informe o nome';
    if (!l.codigo.trim()) return 'Informe o código';
    if (!l.precoReais || l.precoReais <= 0) return 'Informe o preço de venda';
  }
  if (!l.fator || l.fator < 1 || !Number.isInteger(Number(l.fator))) return 'Fator inválido';
  return null;
}

const pendencias = computed(() => (previa.value?.itens ?? []).filter((i) => problemaDa(i)).length);
const contagem = computed(() => {
  const todas = Object.values(linhas);
  return {
    entram: todas.filter((l) => l.acao !== 'ignorar').length,
    novos: todas.filter((l) => l.acao === 'criar').length,
  };
});

const SITUACAO: Record<string, { rotulo: string; classe: string }> = {
  vinculo: { rotulo: 'Reconhecido (já vinculado antes)', classe: 'bg-emerald-50 text-emerald-700' },
  embalagem: { rotulo: 'Reconhecido pelo código da embalagem', classe: 'bg-emerald-50 text-emerald-700' },
  codigo_barras: { rotulo: 'Reconhecido pelo código de barras', classe: 'bg-emerald-50 text-emerald-700' },
};

async function darEntrada() {
  const nota = previa.value;
  if (!nota || pendencias.value || nota.ja_importada_em) return;
  importando.value = true;
  try {
    resultado.value = await importarNotaXml({
      xml: xml.value,
      lancar_contas_pagar: lancarContas.value,
      itens: nota.itens.map((item) => {
        const l = linhas[item.indice];
        if (l.acao === 'ignorar') return { indice: item.indice, acao: 'ignorar', fator: 1 };
        if (l.acao === 'vincular') {
          return {
            indice: item.indice,
            acao: 'vincular',
            produto_id: Number(l.produtoId),
            embalagem_id: l.embalagemId ? Number(l.embalagemId) : null,
            fator: Number(l.fator),
            fator_confirmado: l.fatorConfirmado,
          };
        }
        return {
          indice: item.indice,
          acao: 'criar',
          fator: Number(l.fator),
          fator_confirmado: l.fatorConfirmado,
          novo: {
            nome: l.nome.trim(),
            codigo_produto: l.codigo.trim(),
            codigo_barras: l.codigoBarras.trim() || null,
            unidade_medida: 'UN',
            valor_varejo: Math.round((l.precoReais ?? 0) * 100),
            usar_fiscal_sugerido: true,
          },
        };
      }),
    });
    etapa.value = 'pronto';
    queryClient.invalidateQueries({ queryKey: [PRODUTOS_QUERY_KEY] });
    queryClient.invalidateQueries({ queryKey: [MOVIMENTACOES_QUERY_KEY] });
    toast.success(`NF-e ${nota.numero}: entrada registrada`);
  } catch (erro) {
    toast.error('A entrada não foi feita', getErrorMessage(erro as AxiosError<ApiError>, 'Nada foi gravado. Confira e tente de novo.'));
  } finally {
    importando.value = false;
  }
}

function mandarParaEtiquetas() {
  if (!resultado.value) return;
  emit('etiquetas', resultado.value.entradas);
  emit('close');
}

function formatarData(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso.length === 10 ? `${iso}T12:00:00` : iso).toLocaleDateString('pt-BR');
}

function formatarQtd(n: number): string {
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 3 });
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Entrada por XML da NF-e"
    :subtitle="previa ? `NF-e ${previa.numero}/${previa.serie} · ${previa.fornecedor.fantasia || previa.fornecedor.nome}` : 'Dê entrada na nota de compra do fornecedor'"
    :size="etapa === 'conferencia' ? '4xl' : 'lg'"
    @close="emit('close')"
  >
    <!-- Passo 1: arquivo -->
    <div v-if="etapa === 'arquivo'" class="space-y-4">
      <label
        class="flex flex-col items-center justify-center gap-3 p-10 border-2 border-dashed rounded-2xl cursor-pointer transition-colors"
        :class="arrastando ? 'border-brand-primary bg-brand-primary/5' : 'border-zinc-300 hover:border-brand-primary/60'"
        @dragover.prevent="arrastando = true"
        @dragleave.prevent="arrastando = false"
        @drop.prevent="aoSoltar"
      >
        <FileUp :size="36" class="text-brand-primary" />
        <span class="text-sm font-semibold text-zinc-700">
          {{ lendo ? 'Lendo a nota…' : 'Escolha ou arraste o arquivo .xml da nota' }}
        </span>
        <span class="text-xs text-zinc-500">É o XML que o fornecedor manda por e-mail junto com o DANFE.</span>
        <input type="file" accept=".xml,text/xml,application/xml" class="hidden" :disabled="lendo" @change="aoEscolher" />
      </label>
      <p class="text-xs text-zinc-500">
        Nada é gravado agora: primeiro você confere cada item, depois confirma a entrada.
      </p>
    </div>

    <!-- Passo 2: conferência -->
    <div v-else-if="etapa === 'conferencia' && previa" class="space-y-4">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div class="rounded-xl bg-zinc-50 border border-zinc-200 p-3">
          <span class="block text-[10px] uppercase tracking-wide text-zinc-400 font-semibold">Fornecedor</span>
          <span class="font-semibold text-zinc-800">{{ previa.fornecedor.fantasia || previa.fornecedor.nome }}</span>
          <span class="block text-[11px]" :class="previa.fornecedor.id ? 'text-zinc-500' : 'text-brand-primary'">
            {{ previa.fornecedor.id ? 'Já cadastrado' : 'Será cadastrado' }}
          </span>
        </div>
        <div class="rounded-xl bg-zinc-50 border border-zinc-200 p-3">
          <span class="block text-[10px] uppercase tracking-wide text-zinc-400 font-semibold">Emissão</span>
          <span class="font-semibold text-zinc-800">{{ formatarData(previa.emissao) }}</span>
        </div>
        <div class="rounded-xl bg-zinc-50 border border-zinc-200 p-3">
          <span class="block text-[10px] uppercase tracking-wide text-zinc-400 font-semibold">Valor da nota</span>
          <span class="font-semibold text-zinc-800">{{ formatCurrency(previa.valor_total) }}</span>
        </div>
        <div class="rounded-xl bg-zinc-50 border border-zinc-200 p-3">
          <span class="block text-[10px] uppercase tracking-wide text-zinc-400 font-semibold">Itens</span>
          <span class="font-semibold text-zinc-800">{{ previa.itens.length }}</span>
          <span class="block text-[11px] text-zinc-500">{{ contagem.novos }} a cadastrar</span>
        </div>
      </div>

      <div
        v-for="aviso in previa.avisos"
        :key="aviso"
        class="flex items-start gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800"
      >
        <AlertTriangle :size="15" class="shrink-0" /> {{ aviso }}
      </div>

      <!-- Itens -->
      <div class="space-y-3">
        <div
          v-for="item in previa.itens"
          :key="item.indice"
          class="rounded-xl border p-4 space-y-3"
          :class="[
            linhas[item.indice].acao === 'ignorar' ? 'border-zinc-200 opacity-60' : 'border-zinc-200',
            problemaDa(item) ? 'border-amber-300' : '',
          ]"
        >
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div class="min-w-0">
              <p class="text-sm font-semibold text-zinc-800">
                <span class="text-zinc-400 font-mono mr-1">{{ item.indice }}.</span>{{ item.descricao }}
              </p>
              <p class="text-[11px] text-zinc-500">
                Cód. {{ item.codigo }}<template v-if="item.ean"> · EAN {{ item.ean }}</template>
                · {{ formatarQtd(item.quantidade) }} {{ item.unidade }} · {{ formatCurrency(item.custo_total) }}
                <template v-if="item.fiscal_sugerido.icms_st"> · com ICMS-ST</template>
              </p>
            </div>
            <span
              class="px-2 py-0.5 rounded-full text-[10px] font-bold"
              :class="item.reconhecido_por ? SITUACAO[item.reconhecido_por].classe : 'bg-amber-50 text-amber-700'"
            >
              {{ item.reconhecido_por ? SITUACAO[item.reconhecido_por].rotulo : 'Não reconhecido' }}
            </span>
          </div>

          <!-- Ação -->
          <div class="flex flex-wrap gap-2 text-xs">
            <button
              v-for="opcao in ([
                { acao: 'vincular', rotulo: 'Produto existente', icone: Link2 },
                { acao: 'criar', rotulo: 'Cadastrar novo', icone: PackagePlus },
                { acao: 'ignorar', rotulo: 'Não dar entrada', icone: Ban },
              ] as const)"
              :key="opcao.acao"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border font-semibold transition-colors cursor-pointer"
              :class="linhas[item.indice].acao === opcao.acao
                ? 'border-brand-primary bg-brand-primary/10 text-brand-primary'
                : 'border-zinc-200 text-zinc-500 hover:border-zinc-300'"
              @click="linhas[item.indice].acao = opcao.acao"
            >
              <component :is="opcao.icone" :size="13" /> {{ opcao.rotulo }}
            </button>
          </div>

          <div v-if="linhas[item.indice].acao === 'vincular'" class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
            <div class="md:col-span-6">
              <BaseSelect
                v-model="linhas[item.indice].produtoId"
                label="Produto"
                placeholder="Busque pelo nome"
                :options="produtoOptions"
                @update:model-value="aoTrocarProduto(linhas[item.indice], item)"
              />
            </div>
            <div class="md:col-span-3">
              <BaseSelect
                v-model="linhas[item.indice].embalagemId"
                label="Entra como"
                :options="embalagemOptions(linhas[item.indice])"
                @update:model-value="aoTrocarEmbalagem(linhas[item.indice], item)"
              />
            </div>
            <label class="md:col-span-3 flex flex-col text-xs font-medium text-gray-700 gap-1">
              Unidades por {{ item.unidade }}
              <input
                v-model.number="linhas[item.indice].fator"
                type="number"
                min="1"
                step="1"
                :disabled="!!linhas[item.indice].embalagemId"
                class="px-3 py-2 border border-gray-300 rounded-md text-sm disabled:bg-gray-100"
              />
            </label>
          </div>

          <div v-else-if="linhas[item.indice].acao === 'criar'" class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
            <label class="md:col-span-5 flex flex-col text-xs font-medium text-gray-700 gap-1">
              Nome do produto
              <input v-model="linhas[item.indice].nome" maxlength="255" class="px-3 py-2 border border-gray-300 rounded-md text-sm" />
            </label>
            <label class="md:col-span-3 flex flex-col text-xs font-medium text-gray-700 gap-1">
              Código (SKU)
              <input v-model="linhas[item.indice].codigo" maxlength="100" class="px-3 py-2 border border-gray-300 rounded-md text-sm" />
            </label>
            <label class="md:col-span-2 flex flex-col text-xs font-medium text-gray-700 gap-1">
              Un. por {{ item.unidade }}
              <input
                v-model.number="linhas[item.indice].fator"
                type="number"
                min="1"
                step="1"
                class="px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </label>
            <div class="md:col-span-2">
              <BaseMoneyInput v-model="linhas[item.indice].precoReais" label="Preço de venda (un.)" />
            </div>
            <p class="md:col-span-12 text-[11px] text-zinc-500">
              Código de barras da unidade: <strong>{{ linhas[item.indice].codigoBarras || 'sem código' }}</strong>
              <template v-if="item.fiscal_sugerido.ncm">
                · Fiscal sugerido pela nota: NCM {{ item.fiscal_sugerido.ncm }}
                · {{ item.fiscal_sugerido.csosn ? `CSOSN ${item.fiscal_sugerido.csosn}` : `CST ${item.fiscal_sugerido.cst_icms}` }}
                · CFOP {{ item.fiscal_sugerido.cfop_padrao }}
                <span class="text-zinc-400">(confira com o contador)</span>
              </template>
            </p>
          </div>

          <!-- CX/FD sem o fator: pergunta direto, como os sistemas de mercado
               fazem com o "fator de conversão". O servidor recusa sem isto. -->
          <div
            v-if="fatorPendente(item)"
            class="flex flex-wrap items-center gap-3 p-3 rounded-lg bg-amber-50 border border-amber-300 text-xs text-amber-900"
          >
            <AlertTriangle :size="15" class="shrink-0 text-amber-600" />
            <span class="flex-1 min-w-48">
              A nota diz <strong>{{ formatarQtd(item.quantidade) }} {{ item.unidade }}</strong>, mas não diz quantas
              unidades vêm em cada {{ item.unidade }}. Sem isso, entrariam só
              {{ formatarQtd(item.quantidade) }} unidades no estoque.
            </span>
            <label class="flex items-center gap-2 font-semibold">
              Unidades por {{ item.unidade }}
              <input
                v-model.number="linhas[item.indice].fator"
                type="number"
                min="1"
                step="1"
                class="w-20 px-2 py-1.5 border border-amber-300 rounded-md text-sm bg-white"
              />
            </label>
            <button
              type="button"
              class="px-3 py-1.5 rounded-lg border border-amber-300 bg-white font-semibold hover:bg-amber-100 cursor-pointer"
              @click="confirmarFatorUm(item)"
            >
              É 1 unidade mesmo
            </button>
          </div>

          <!-- Resultado da linha -->
          <div
            v-if="linhas[item.indice].acao !== 'ignorar'"
            class="flex flex-wrap items-center justify-between gap-2 text-xs pt-2 border-t border-zinc-100"
          >
            <span class="text-zinc-600">
              Na nota <strong class="text-zinc-800">{{ formatarQtd(item.quantidade) }} {{ item.unidade }}</strong>
              → no estoque <strong class="text-zinc-800">{{ formatarQtd(unidades(item)) }} un</strong>
              a <strong class="text-zinc-800">{{ formatCurrency(custoUnidade(item)) }}</strong> cada
              <template v-if="custoAnterior(item) !== null && !divergenciaCusto(item)">
                <span class="text-zinc-400"> (custo atual {{ formatCurrency(custoAnterior(item)!) }})</span>
              </template>
            </span>
            <span v-if="problemaDa(item)" class="text-amber-700 font-semibold">{{ problemaDa(item) }}</span>
          </div>
          <p
            v-if="linhas[item.indice].acao !== 'ignorar' && divergenciaCusto(item)"
            class="flex items-start gap-1.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg p-2"
          >
            <AlertTriangle :size="14" class="shrink-0 mt-px" />
            <span>
              Custo {{ divergenciaCusto(item)!.pct > 0 ? `${divergenciaCusto(item)!.pct}% maior` : `${-divergenciaCusto(item)!.pct}% menor` }}
              que o atual ({{ formatCurrency(divergenciaCusto(item)!.anterior) }} → {{ formatCurrency(custoUnidade(item)) }}).
              Confira as unidades por {{ item.unidade }} antes de dar entrada.
            </span>
          </p>
        </div>
      </div>

      <!-- Parcelas -->
      <div v-if="previa.duplicatas.length" class="rounded-xl border border-zinc-200 p-4 space-y-2">
        <label
          class="flex items-center gap-2 text-sm font-semibold text-zinc-700 select-none"
          :class="previa.financeiro_disponivel ? 'cursor-pointer' : 'opacity-60'"
        >
          <input
            v-model="lancarContas"
            type="checkbox"
            class="accent-brand-primary"
            :disabled="!previa.financeiro_disponivel"
          />
          Lançar {{ previa.duplicatas.length }} parcela(s) no contas a pagar
          <span v-if="!previa.financeiro_disponivel" class="text-xs font-normal text-zinc-500">(módulo Financeiro não contratado)</span>
        </label>
        <ul class="text-xs text-zinc-600 space-y-0.5 pl-6">
          <li v-for="d in previa.duplicatas" :key="d.numero + d.vencimento">
            {{ d.numero || '—' }} · vence {{ formatarData(d.vencimento) }} · {{ formatCurrency(d.valor) }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Passo 3: pronto -->
    <div v-else-if="etapa === 'pronto' && resultado" class="space-y-4 text-center py-4">
      <CheckCircle2 :size="44" class="mx-auto text-emerald-500" />
      <p class="text-base font-semibold text-zinc-800">Entrada registrada</p>
      <ul class="text-sm text-zinc-600 space-y-1">
        <li>{{ resultado.itens_lancados }} item(ns) com entrada no estoque</li>
        <li v-if="resultado.produtos_criados">{{ resultado.produtos_criados }} produto(s) cadastrado(s)</li>
        <li v-if="resultado.itens_ignorados">{{ resultado.itens_ignorados }} item(ns) sem entrada</li>
        <li v-if="resultado.fornecedor_criado">Fornecedor cadastrado</li>
        <li v-if="resultado.contas_pagar_lancadas">{{ resultado.contas_pagar_lancadas }} parcela(s) no contas a pagar</li>
      </ul>
    </div>

    <template #footer>
      <div class="flex flex-wrap items-center justify-end gap-3">
        <template v-if="etapa === 'conferencia'">
          <span v-if="pendencias" class="mr-auto text-xs text-amber-700 font-semibold">
            {{ pendencias }} item(ns) a completar
          </span>
          <BaseButton variant="secondary" @click="etapa = 'arquivo'">Outro arquivo</BaseButton>
          <BaseButton
            :disabled="!!pendencias || importando || !!previa?.ja_importada_em || !contagem.entram"
            :is-loading="importando"
            @click="darEntrada"
          >
            Dar entrada
          </BaseButton>
        </template>
        <template v-else-if="etapa === 'pronto'">
          <BaseButton variant="secondary" @click="emit('close')">Fechar</BaseButton>
          <BaseButton v-if="resultado?.entradas.length" class="flex items-center gap-2" @click="mandarParaEtiquetas">
            <Tag :size="15" /> Etiquetas desta entrada
          </BaseButton>
        </template>
        <BaseButton v-else variant="secondary" @click="emit('close')">Cancelar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
