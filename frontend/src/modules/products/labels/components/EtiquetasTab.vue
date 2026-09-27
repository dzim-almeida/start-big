<script setup lang="ts">
/**
 * @fileoverview Aba Etiquetas do Estoque (docs/etiquetas-plano.md, fases 1 e 2).
 *
 * Duas sub-abas: Estoque (catálogo na largura toda; a fila abre num painel
 * pela direita) e Envio (etiqueta de volume e DANFE Simplificado, fase 5).
 */
import { computed, onUnmounted, ref, watch } from 'vue';
import { Tags, Truck } from 'lucide-vue-next';

import { useToast } from '@/shared/composables/useToast';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';
import { useImpressaoStore, type ConfigImpressao } from '@/shared/stores/impressao.store';
import EtiquetasImpressao from '@/shared/etiquetas/components/EtiquetasImpressao.vue';
import { useImpressaoEtiquetas } from '@/shared/etiquetas/useImpressaoEtiquetas';
import { PRESET_PADRAO } from '@/shared/etiquetas/presets';
import { valoresDoProduto, valorDoCodigo } from '@/shared/etiquetas/campos';
import { expandir } from '@/shared/etiquetas/paginacao';
import { definicaoDeTeste, etiquetasDeTeste } from '@/shared/etiquetas/teste';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

import ProdutosEtiquetaTable from './estoque/ProdutosEtiquetaTable.vue';
import EnvioEtiquetasPanel from './envio/EnvioEtiquetasPanel.vue';
import type { TipoOrigemEnvio } from '@/shared/etiquetas/envio';
import FilaEtiquetasDrawer from './estoque/FilaEtiquetasDrawer.vue';
import EntradasRecentesModal from './estoque/EntradasRecentesModal.vue';
import CalibracaoEtiquetaModal from './estoque/CalibracaoEtiquetaModal.vue';
import ModelosEtiquetaModal from './modelo/ModelosEtiquetaModal.vue';
import { useFilaEtiquetasStore } from '../store/filaEtiquetas.store';
import { useModelosEtiqueta } from '../composables/useModelosEtiqueta';
import type { LinhaFila } from '../types/etiquetas.types';
import type { ModeloEtiqueta } from '@/shared/etiquetas/modelo';

/** Acima disto o diálogo de impressão do Windows fica lento demais para montar. */
const MAX_POR_IMPRESSAO = 2000;

const props = defineProps<{
  /** Atalho da lista de vendas: abre direto na sub-aba Envio com esta venda. */
  envioInicial?: { tipo: TipoOrigemEnvio; id: number } | null;
  produtos: ProdutoRead[];
  isLoading?: boolean;
}>();

const toast = useToast();
const fila = useFilaEtiquetasStore();
const impressaoStore = useImpressaoStore();
const { companyInfo } = useCompanyPrintInfo();
const { todos: modelos, modelosDaLoja } = useModelosEtiqueta();
const { trabalho, imprimir } = useImpressaoEtiquetas();

// O painel mora dentro da aba: saindo dela, não pode reabrir sozinho na volta.
onUnmounted(() => (fila.painelAberto = false));

const subAba = ref<'estoque' | 'envio'>(props.envioInicial ? 'envio' : 'estoque');
watch(
  () => props.envioInicial,
  (origem) => {
    if (origem) subAba.value = 'envio';
  },
);

const isEntradasOpen = ref(false);
const isModelosOpen = ref(false);
/** Modelo que o atalho "Editar layout" abre direto no editor; nulo = lista de modelos. */
const modeloParaEditor = ref<ModeloEtiqueta | null>(null);

function abrirModelos(noEditor: ModeloEtiqueta | null) {
  modeloParaEditor.value = noEditor;
  isModelosOpen.value = true;
}
const isCalibracaoOpen = ref(false);

// --- Modelo (lembrado por terminal) ---

const chaveModelo = ref<string>(impressaoStore.config.etiqueta_modelo ?? PRESET_PADRAO.chave);
// Modelo lembrado que foi excluído (em outro terminal, inclusive) cai no padrão.
const modelo = computed(() => modelos.value.find((m) => m.chave === chaveModelo.value) ?? PRESET_PADRAO);

watch(chaveModelo, (chave) => {
  if (chave !== impressaoStore.config.etiqueta_modelo) {
    impressaoStore.salvar({ ...impressaoStore.config, etiqueta_modelo: chave });
  }
});

const pular = ref(0);
watch(chaveModelo, () => (pular.value = 0));

// --- Fila ---

const produtosPorId = computed(() => new Map(props.produtos.map((p) => [p.id, p])));
const idsNaFila = computed(() => new Set(fila.itens.map((i) => i.produtoId)));
const idsAtivos = computed(() => new Set(props.produtos.filter((p) => p.ativo).map((p) => p.id)));

const linhas = computed<LinhaFila[]>(() =>
  fila.itens.flatMap(({ produtoId, quantidade }) => {
    const produto = produtosPorId.value.get(produtoId);
    if (!produto) return [];
    const valores = valoresDoProduto(produto, { empresaNome: companyInfo.value.nome });
    return [{ produto, quantidade, valores, semCodigo: !valorDoCodigo(valores, 'produto.codigo_barras') }];
  }),
);

const totalEtiquetas = computed(() => linhas.value.reduce((soma, l) => soma + l.quantidade, 0));

function adicionarEntradas(itens: { produtoId: number; quantidade: number }[]) {
  itens.forEach((i) => fila.adicionar(i.produtoId, i.quantidade));
  isEntradasOpen.value = false;
  fila.painelAberto = true;
}

// --- Impressão ---

function deslocamento() {
  return {
    deslocamentoX: impressaoStore.config.etiqueta_deslocamento_x_mm ?? 0,
    deslocamentoY: impressaoStore.config.etiqueta_deslocamento_y_mm ?? 0,
  };
}

function imprimirFila() {
  if (totalEtiquetas.value > MAX_POR_IMPRESSAO) {
    toast.warning(
      `No máximo ${MAX_POR_IMPRESSAO} etiquetas por impressão`,
      `A fila tem ${totalEtiquetas.value}. Imprima em partes.`,
    );
    return;
  }
  const etiquetas = expandir(linhas.value.map((l) => ({ item: l.valores, quantidade: l.quantidade })));
  imprimir({ definicao: modelo.value.definicao, etiquetas, pular: pular.value, ...deslocamento() });
}

function imprimirTeste(config?: ConfigImpressao) {
  const definicao = definicaoDeTeste(modelo.value.definicao, modelo.value.nome);
  const cfg = config ?? impressaoStore.config;
  imprimir(
    {
      definicao,
      etiquetas: etiquetasDeTeste(definicao),
      pular: 0,
      deslocamentoX: cfg.etiqueta_deslocamento_x_mm ?? 0,
      deslocamentoY: cfg.etiqueta_deslocamento_y_mm ?? 0,
    },
    cfg,
  );
}
</script>

<template>
  <div class="inline-flex p-1 rounded-xl bg-white border border-zinc-200">
    <button type="button" :class="['sub-aba', subAba === 'estoque' && 'sub-aba--ativa']" @click="subAba = 'estoque'">
      <Tags :size="15" />
      Estoque
    </button>
    <button type="button" :class="['sub-aba', subAba === 'envio' && 'sub-aba--ativa']" @click="subAba = 'envio'">
      <Truck :size="15" />
      Envio
    </button>
  </div>

  <EnvioEtiquetasPanel v-if="subAba === 'envio'" :origem-inicial="envioInicial" />

  <template v-else>
    <ProdutosEtiquetaTable
      :produtos="produtos"
      :ids-na-fila="idsNaFila"
      :total-etiquetas="totalEtiquetas"
      :is-loading="isLoading"
      @adicionar="fila.adicionar($event)"
      @entradas="isEntradasOpen = true"
      @abrir-fila="fila.painelAberto = true"
    />

    <FilaEtiquetasDrawer
      v-model:chave-modelo="chaveModelo"
      v-model:pular="pular"
      :is-open="fila.painelAberto"
      :linhas="linhas"
      :modelos="modelos"
      :modelo="modelo"
      :total-etiquetas="totalEtiquetas"
      @close="fila.painelAberto = false"
      @update:quantidade="fila.definirQuantidade"
      @remover="fila.remover"
      @limpar="fila.limpar"
      @imprimir="imprimirFila"
      @imprimir-teste="imprimirTeste()"
      @gerenciar-modelos="abrirModelos(null)"
      @editar-layout="abrirModelos(modelo)"
      @calibrar="isCalibracaoOpen = true"
    />
  </template>

  <EntradasRecentesModal
    :is-open="isEntradasOpen"
    :ids-ativos="idsAtivos"
    @close="isEntradasOpen = false"
    @adicionar="adicionarEntradas"
  />

  <ModelosEtiquetaModal
    :is-open="isModelosOpen"
    :modelos="modelosDaLoja"
    :abrir-no-editor="modeloParaEditor"
    @close="isModelosOpen = false"
    @salvo="chaveModelo = $event"
  />

  <CalibracaoEtiquetaModal
    :is-open="isCalibracaoOpen"
    @close="isCalibracaoOpen = false"
    @testar="imprimirTeste"
  />

  <EtiquetasImpressao v-if="trabalho" v-bind="trabalho" />
</template>

<style scoped>
.sub-aba {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #71717a;
  cursor: pointer;
}
.sub-aba:hover {
  color: var(--color-brand-primary);
}
.sub-aba--ativa,
.sub-aba--ativa:hover {
  background: var(--color-brand-primary);
  color: #fff;
}
</style>
