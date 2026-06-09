<script setup lang="ts">
import { reactive, watch } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'
import { ACAO_FINALIZAR_OPTIONS } from '@/modules/configuracoes/schemas/configuracoes.schema'

const configStore = useConfiguracoesStore()
const {
  permitirDesconto,
  descontoMaximoPercent,
  permitirVendaEstoqueZerado,
  exigirClienteIdentificado,
  acaoAoFinalizar,
} = storeToRefs(configStore)

const form = reactive({
  vendas: {
    permitir_desconto: permitirDesconto.value,
    desconto_maximo_percent: descontoMaximoPercent.value,
    exigir_cliente_identificado: exigirClienteIdentificado.value,
    acao_ao_finalizar: acaoAoFinalizar.value,
  },
  estoque: {
    permitir_venda_estoque_zerado: permitirVendaEstoqueZerado.value,
  },
})

watch(() => configStore.configVendas, () => {
  form.vendas.permitir_desconto = permitirDesconto.value
  form.vendas.desconto_maximo_percent = descontoMaximoPercent.value
  form.vendas.exigir_cliente_identificado = exigirClienteIdentificado.value
  form.vendas.acao_ao_finalizar = acaoAoFinalizar.value
})

watch(() => configStore.configProdutos, () => {
  form.estoque.permitir_venda_estoque_zerado = permitirVendaEstoqueZerado.value
})

defineExpose({ form })
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Regras de Vendas</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Defina as regras e limitações para o processo de vendas</p>
    </div>

    <!-- Descontos -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Descontos</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir desconto em vendas</p>
          <p class="text-xs text-zinc-500 mt-0.5">Habilita o campo de desconto no carrinho</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.permitir_desconto ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.permitir_desconto = !form.vendas.permitir_desconto"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.permitir_desconto ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="py-3 border-b border-zinc-100">
        <label class="text-xs font-medium text-zinc-600">Desconto máximo permitido (%)</label>
        <input
          v-model.number="form.vendas.desconto_maximo_percent"
          type="number"
          min="0"
          max="100"
          :disabled="!form.vendas.permitir_desconto"
          class="mt-1.5 w-full border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:opacity-40 disabled:cursor-not-allowed"
        />
      </div>
    </div>

    <!-- Estoque e Clientes -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Estoque e Clientes</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir venda sem estoque</p>
          <p class="text-xs text-zinc-500 mt-0.5">Vende mesmo quando o produto está zerado</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.estoque.permitir_venda_estoque_zerado ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.estoque.permitir_venda_estoque_zerado = !form.estoque.permitir_venda_estoque_zerado"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.estoque.permitir_venda_estoque_zerado ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir cliente identificado</p>
          <p class="text-xs text-zinc-500 mt-0.5">Toda venda deve ter um cliente vinculado</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.exigir_cliente_identificado ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.exigir_cliente_identificado = !form.vendas.exigir_cliente_identificado"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.exigir_cliente_identificado ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Comportamento -->
    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Comportamento</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Ação ao finalizar venda</label>
        <div class="relative">
          <select
            v-model="form.vendas.acao_ao_finalizar"
            class="w-full appearance-none border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          >
            <option v-for="opt in ACAO_FINALIZAR_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
          <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none" />
        </div>
      </div>
    </div>
  </div>
</template>
