<script setup lang="ts">
import { reactive, watch } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'

const configStore = useConfiguracoesStore()
const {
  exigirCodigoBarras,
  exigirCategoria,
  exigirPrecoCusto,
  margemLucroPadrao,
  utilizarPrecoAtacado,
  permitirVendaEstoqueZerado,
  quantidadeMinimaPadrao,
  unidadeMedidaPadrao,
} = storeToRefs(configStore)

const UNIDADE_MEDIDA_OPTIONS = [
  { value: 'UN', label: 'Unidade (UN)' },
  { value: 'KG', label: 'Quilograma (KG)' },
  { value: 'G', label: 'Grama (G)' },
  { value: 'L', label: 'Litro (L)' },
  { value: 'ML', label: 'Mililitro (ML)' },
  { value: 'M', label: 'Metro (M)' },
  { value: 'CM', label: 'Centímetro (CM)' },
  { value: 'CX', label: 'Caixa (CX)' },
  { value: 'PC', label: 'Peça (PC)' },
  { value: 'PCT', label: 'Pacote (PCT)' },
]

const form = reactive({
  exigir_codigo_barras: exigirCodigoBarras.value,
  exigir_categoria: exigirCategoria.value,
  exigir_preco_custo: exigirPrecoCusto.value,
  margem_lucro_padrao: margemLucroPadrao.value,
  utilizar_preco_atacado: utilizarPrecoAtacado.value,
  permitir_venda_estoque_zerado: permitirVendaEstoqueZerado.value,
  quantidade_minima_padrao: quantidadeMinimaPadrao.value,
  unidade_medida_padrao: unidadeMedidaPadrao.value,
})

watch(() => configStore.configProdutos, () => {
  form.exigir_codigo_barras = exigirCodigoBarras.value
  form.exigir_categoria = exigirCategoria.value
  form.exigir_preco_custo = exigirPrecoCusto.value
  form.margem_lucro_padrao = margemLucroPadrao.value
  form.utilizar_preco_atacado = utilizarPrecoAtacado.value
  form.permitir_venda_estoque_zerado = permitirVendaEstoqueZerado.value
  form.quantidade_minima_padrao = quantidadeMinimaPadrao.value
  form.unidade_medida_padrao = unidadeMedidaPadrao.value
})

defineExpose({ form })
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Produtos e Estoque</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Configure os campos, regras e automações do cadastro de produtos</p>
    </div>

    <!-- Campos Obrigatórios -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Campos Obrigatórios</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir Código de Barras</p>
          <p class="text-xs text-zinc-500 mt-0.5">Se desativado, o sistema gera um código interno sequencial automaticamente</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_codigo_barras ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_codigo_barras = !form.exigir_codigo_barras"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_codigo_barras ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir Categoria</p>
          <p class="text-xs text-zinc-500 mt-0.5">Obriga a vincular o produto a uma categoria para organizar relatórios</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_categoria ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_categoria = !form.exigir_categoria"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_categoria ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir Preço de Custo</p>
          <p class="text-xs text-zinc-500 mt-0.5">Garante o preenchimento do custo para cálculo de lucro real nos relatórios</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_preco_custo ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_preco_custo = !form.exigir_preco_custo"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_preco_custo ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Preços e Automações -->
    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Preços e Automações</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Margem de Lucro Padrão (%)</label>
        <input
          v-model.number="form.margem_lucro_padrao"
          type="number"
          min="0"
          max="1000"
          step="0.1"
          placeholder="Ex: 30"
          class="w-full border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        />
        <p class="text-xs text-zinc-400">Ao digitar o custo no cadastro, o sistema sugere automaticamente o preço de varejo</p>
      </div>

      <div class="flex items-center justify-between py-3 border-t border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Utilizar e exibir Preço de Atacado</p>
          <p class="text-xs text-zinc-500 mt-0.5">Se desativado, oculta os campos de atacado no cadastro e na tela de vendas</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.utilizar_preco_atacado ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.utilizar_preco_atacado = !form.utilizar_preco_atacado"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.utilizar_preco_atacado ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Controle de Estoque -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Controle de Estoque</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir faturamento com estoque zerado/negativo</p>
          <p class="text-xs text-zinc-500 mt-0.5">O caixa não trava com saldo zerado. O gerente corrige o estoque depois</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.permitir_venda_estoque_zerado ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.permitir_venda_estoque_zerado = !form.permitir_venda_estoque_zerado"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.permitir_venda_estoque_zerado ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Padrões de Cadastro -->
    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Padrões de Cadastro</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Quantidade Mínima Padrão para Alerta</label>
        <input
          v-model.number="form.quantidade_minima_padrao"
          type="number"
          min="0"
          placeholder="5"
          class="w-full border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        />
        <p class="text-xs text-zinc-400">Valor pré-preenchido no campo "Quantidade Mínima" ao criar um novo produto</p>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Unidade de Medida Padrão</label>
        <div class="relative">
          <select
            v-model="form.unidade_medida_padrao"
            class="w-full appearance-none border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          >
            <option v-for="opt in UNIDADE_MEDIDA_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
          <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none" />
        </div>
        <p class="text-xs text-zinc-400">Valor pré-selecionado no dropdown ao criar um novo produto</p>
      </div>
    </div>
  </div>
</template>
