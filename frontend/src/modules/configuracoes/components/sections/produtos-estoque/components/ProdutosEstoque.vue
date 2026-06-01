<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Produtos e Estoque</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Gerencie as regras de controle de estoque e produtos</p>
    </div>

    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Controle de Estoque</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Ativar controle de estoque</p>
          <p class="text-xs text-zinc-500 mt-0.5">Registra entradas e saídas de produtos automaticamente</p>
        </div>
        <div class="relative w-9 h-4.5 bg-brand-primary rounded-full shrink-0">
          <span class="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Alertar quando estoque estiver baixo</p>
          <p class="text-xs text-zinc-500 mt-0.5">Notifica quando atingir a quantidade mínima</p>
        </div>
        <div class="relative w-9 h-4.5 bg-brand-primary rounded-full shrink-0">
          <span class="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="py-3 border-b border-zinc-100">
        <label class="text-xs font-medium text-zinc-600">Quantidade mínima para alerta</label>
        <div class="mt-1.5 border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700">
          5
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Produtos</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Unidade de medida padrão</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Unidade (UN)</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-t border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exibir código de barras no produto</p>
          <p class="text-xs text-zinc-500 mt-0.5">Mostra o código EAN na listagem de produtos</p>
        </div>
        <div class="relative w-9 h-4.5 bg-brand-primary rounded-full shrink-0">
          <span class="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>
    </div>
  </div>
</template>
