<script setup lang="ts">
/**
 * @fileoverview Aba Etiquetas do Estoque (docs/etiquetas-plano.md, fases 1 e 2).
 *
 * Catálogo à esquerda, fila de impressão à direita. A sub-aba "Envio" (fase 5)
 * entra aqui quando existir — sem aba morta antes disso.
 */
import { computed, ref, watch } from 'vue';

import { useToast } from '@/shared/composables/useToast';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import EtiquetasImpressao from '@/shared/etiquetas/components/EtiquetasImpressao.vue';
import { useImpressaoEtiquetas } from '@/shared/etiquetas/useImpressaoEtiquetas';
import { PRESET_PADRAO } from '@/shared/etiquetas/presets';
import { valoresDoProduto, valorDoCodigo } from '@/shared/etiquetas/campos';
import { expandir } from '@/shared/etiquetas/paginacao';
import { definicaoDeTeste, etiquetasDeTeste } from '@/shared/etiquetas/teste';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

import ProdutosEtiquetaTable from './estoque/ProdutosEtiquetaTable.vue';
import FilaEtiquetasCard from './estoque/FilaEtiquetasCard.vue';
import EntradasRecentesModal from './estoque/EntradasRecentesModal.vue';
import CalibracaoEtiquetaModal from './estoque/CalibracaoEtiquetaModal.vue';
import ModelosEtiquetaModal from './modelo/ModelosEtiquetaModal.vue';
import { useFilaEtiquetasStore } from '../store/filaEtiquetas.store';
import { useModelosEtiqueta } from '../composables/useModelosEtiqueta';
import type { LinhaFila } from '../types/etiquetas.types';

/** Acima disto o diálogo de impressão do Windows fica lento demais para montar. */
const MAX_POR_IMPRESSAO = 2000;

const props = defineProps<{
  produtos: ProdutoRead[];
  isLoading?: boolean;
}>();

const toast = useToast();
const fila = useFilaEtiquetasStore();
const impressaoStore = useImpressaoStore();
const { companyInfo } = useCompanyPrintInfo();
const { todos: modelos, modelosDaLoja } = useModelosEtiqueta();
const { trabalho, imprimir } = useImpressaoEtiquetas();

const isEntradasOpen = ref(false);
const isModelosOpen = ref(false);
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
  toast.success('Entradas adicionadas à fila');
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

function imprimirTeste(ajuste?: { deslocamentoX: number; deslocamentoY: number }) {
  const definicao = definicaoDeTeste(modelo.value.definicao, modelo.value.nome);
  imprimir({ definicao, etiquetas: etiquetasDeTeste(definicao), pular: 0, ...(ajuste ?? deslocamento()) });
}
</script>

<template>
  <div class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
    <ProdutosEtiquetaTable
      class="xl:col-span-7"
      :produtos="produtos"
      :ids-na-fila="idsNaFila"
      :is-loading="isLoading"
      @adicionar="fila.adicionar($event)"
      @entradas="isEntradasOpen = true"
    />

    <FilaEtiquetasCard
      v-model:chave-modelo="chaveModelo"
      v-model:pular="pular"
      class="xl:col-span-5 xl:sticky xl:top-4"
      :linhas="linhas"
      :modelos="modelos"
      :modelo="modelo"
      :total-etiquetas="totalEtiquetas"
      @update:quantidade="fila.definirQuantidade"
      @remover="fila.remover"
      @limpar="fila.limpar"
      @imprimir="imprimirFila"
      @imprimir-teste="imprimirTeste()"
      @gerenciar-modelos="isModelosOpen = true"
      @calibrar="isCalibracaoOpen = true"
    />
  </div>

  <EntradasRecentesModal
    :is-open="isEntradasOpen"
    :ids-ativos="idsAtivos"
    @close="isEntradasOpen = false"
    @adicionar="adicionarEntradas"
  />

  <ModelosEtiquetaModal
    :is-open="isModelosOpen"
    :modelos="modelosDaLoja"
    @close="isModelosOpen = false"
    @salvo="chaveModelo = $event"
  />

  <CalibracaoEtiquetaModal
    :is-open="isCalibracaoOpen"
    @close="isCalibracaoOpen = false"
    @testar="(x, y) => imprimirTeste({ deslocamentoX: x, deslocamentoY: y })"
  />

  <EtiquetasImpressao v-if="trabalho" v-bind="trabalho" />
</template>
