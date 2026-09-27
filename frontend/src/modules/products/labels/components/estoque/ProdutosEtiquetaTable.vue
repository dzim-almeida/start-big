<script setup lang="ts">
/**
 * @fileoverview Catálogo de onde o lojista escolhe o que vai para a fila de etiquetas.
 * Mostra, por produto, COMO o código vai sair no papel — um EAN com dígito
 * errado é descoberto aqui, e não na frente do leitor do caixa.
 */
import { computed, ref, watch } from 'vue';
import { Plus, PackagePlus, Check, Tags } from 'lucide-vue-next';

import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import { correspondeBusca } from '@/shared/utils/busca';
import { formatCurrency } from '@/shared/utils/finance';
import { resolverCodigo, nomeSimbologia } from '@/shared/etiquetas/codigoBarras';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

const ITENS_POR_PAGINA = 8;

const props = defineProps<{
  produtos: ProdutoRead[];
  idsNaFila: Set<number>;
  totalEtiquetas: number;
  isLoading?: boolean;
}>();

const emit = defineEmits<{
  adicionar: [produtoId: number];
  entradas: [];
  abrirFila: [];
}>();

const busca = ref<string | null>('');
const categoria = ref<string | null>(null);
const paginaAtual = ref(1);

const ativos = computed(() => props.produtos.filter((p) => p.ativo));

const filtroCategoria = computed(() => {
  const config: Record<string, { label: string; class: string; color: string }> = {};
  const categorias = new Set(ativos.value.map((p) => (p.categoria || 'SEM CATEGORIA').trim().toUpperCase()));
  for (const cat of [...categorias].sort((a, b) => a.localeCompare(b, 'pt-BR'))) {
    config[cat] = { label: cat, class: 'bg-violet-50 text-violet-600 border border-violet-200', color: 'bg-violet-500' };
  }
  return config;
});

const filtrados = computed(() => {
  const termo = (busca.value || '').trim();
  return ativos.value.filter((p) => {
    if (categoria.value && (p.categoria || 'SEM CATEGORIA').trim().toUpperCase() !== categoria.value) return false;
    if (!termo) return true;
    return correspondeBusca(termo, [p.nome, p.codigo_produto, p.codigo_barras, p.marca, p.categoria]);
  });
});

const totalPaginas = computed(() => Math.max(1, Math.ceil(filtrados.value.length / ITENS_POR_PAGINA)));
const paginados = computed(() =>
  filtrados.value.slice((paginaAtual.value - 1) * ITENS_POR_PAGINA, paginaAtual.value * ITENS_POR_PAGINA),
);

watch([busca, categoria], () => (paginaAtual.value = 1));

/** Como o código deste produto sai no papel. */
function situacaoCodigo(p: ProdutoRead): { rotulo: string; classe: string } {
  const codigo = resolverCodigo(p.codigo_barras || p.codigo_produto);
  if (!codigo) return { rotulo: 'Sem código', classe: 'bg-red-50 text-red-600 border border-red-200' };
  if (codigo.simbologia === 'CODE128') {
    return p.codigo_barras
      ? { rotulo: 'EAN inválido', classe: 'bg-amber-50 text-amber-700 border border-amber-200' }
      : { rotulo: 'Código interno', classe: 'bg-zinc-100 text-zinc-600 border border-zinc-200' };
  }
  return { rotulo: nomeSimbologia(codigo.simbologia), classe: 'bg-emerald-50 text-emerald-700 border border-emerald-200' };
}
</script>

<template>
  <!--
    Barra própria, no mesmo desenho da aba Estoque: a toolbar do
    BaseTableContainer tem teto de meia tela (lg:max-w-1/2), pensado para
    busca + um filtro — com os dois botões de ação a busca ficava espremida.
  -->
  <div class="flex flex-wrap gap-3 p-4 bg-white rounded-2xl">
    <BaseSearchInput
      class="md:max-w-2/3 lg:max-w-1/2"
      v-model="busca"
      placeholder="Buscar por nome, código ou EAN..."
    />
    <BaseFilter v-model="categoria" :filter-config="filtroCategoria" title="Filtrar por Categoria" button-label="Categoria" />
    <div class="ml-auto flex flex-wrap gap-3">
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-xl border border-zinc-200 text-sm font-medium text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300 transition-colors cursor-pointer shrink-0"
        title="Adicionar à fila os produtos que entraram no estoque"
        @click="emit('entradas')"
      >
        <PackagePlus :size="16" />
        Entradas recentes
      </button>
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-semibold hover:bg-brand-primary-hover transition-colors cursor-pointer shrink-0"
        @click="emit('abrirFila')"
      >
        <Tags :size="16" />
        Fila de impressão
        <span class="min-w-6 px-1.5 py-0.5 rounded-full bg-white/20 text-xs font-bold text-center">{{ totalEtiquetas }}</span>
      </button>
    </div>
  </div>

  <BaseTableContainer
    :is-loading="isLoading"
    :is-empty="filtrados.length === 0"
    :current-page="paginaAtual"
    :total-pages="totalPaginas"
    :total-items="filtrados.length"
    item-label="produto"
    empty-title="Nenhum produto encontrado"
    empty-description="Ajuste a busca ou o filtro de categoria."
    @update:current-page="paginaAtual = $event"
  >

    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-120">
        <thead>
          <tr class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100">
            <th class="px-4 md:px-6 py-3 md:py-4">Produto</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Preço</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Código na etiqueta</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right">Fila</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr v-for="produto in paginados" :key="produto.id" class="hover:bg-zinc-50/50 transition-colors">
            <td class="px-4 md:px-6 py-3">
              <div class="flex flex-col">
                <span class="text-sm font-medium text-zinc-900">{{ produto.nome }}</span>
                <span class="text-xs text-zinc-400 font-mono">
                  {{ produto.codigo_barras || produto.codigo_produto || '—' }}
                </span>
              </div>
            </td>
            <td class="px-4 md:px-6 py-3 text-sm text-zinc-700 whitespace-nowrap">
              {{ formatCurrency(produto.estoque.valor_varejo) }}
            </td>
            <td class="px-4 md:px-6 py-3">
              <span :class="['px-2 py-1 rounded-full text-[10px] font-bold whitespace-nowrap', situacaoCodigo(produto).classe]">
                {{ situacaoCodigo(produto).rotulo }}
              </span>
            </td>
            <td class="px-4 md:px-6 py-3 text-right">
              <button
                :class="[
                  'inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors cursor-pointer',
                  idsNaFila.has(produto.id)
                    ? 'bg-brand-primary/10 text-brand-primary border-brand-primary/30 hover:bg-brand-primary/20'
                    : 'text-zinc-600 border-zinc-200 hover:text-brand-primary hover:border-brand-primary',
                ]"
                :title="idsNaFila.has(produto.id) ? 'Já está na fila — clique para somar mais uma' : 'Adicionar à fila'"
                @click="emit('adicionar', produto.id)"
              >
                <Check v-if="idsNaFila.has(produto.id)" :size="14" />
                <Plus v-else :size="14" />
                {{ idsNaFila.has(produto.id) ? 'Na fila' : 'Adicionar' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </BaseTableContainer>
</template>
