<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Regras de Vendas</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Defina as regras e limitações para o processo de vendas</p>
    </div>

    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Descontos</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir desconto em vendas</p>
          <p class="text-xs text-zinc-500 mt-0.5">Habilita o campo de desconto no carrinho</p>
        </div>
        <div class="relative w-9 h-4.5 bg-brand-primary rounded-full shrink-0">
          <span class="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="py-3 border-b border-zinc-100">
        <label class="text-xs font-medium text-zinc-600">Desconto máximo permitido (%)</label>
        <div class="mt-1.5 border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700">
          30
        </div>
      </div>
    </div>

    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Estoque e Clientes</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir venda sem estoque</p>
          <p class="text-xs text-zinc-500 mt-0.5">Vende mesmo quando o produto está zerado</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir cliente identificado</p>
          <p class="text-xs text-zinc-500 mt-0.5">Toda venda deve ter um cliente vinculado</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>
    </div>

    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Comportamento</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Ação ao finalizar venda</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Perguntar o que fazer</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>
    </div>
  </div>
</template>
