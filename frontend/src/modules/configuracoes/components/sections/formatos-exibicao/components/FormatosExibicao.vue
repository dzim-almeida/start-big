<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Formatos e Exibição</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Personalize como datas, valores e informações são exibidos</p>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Data e Hora</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Formato de data</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">DD/MM/AAAA</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Formato de hora</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">24 horas (00:00)</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Valores</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Separador de milhar</p>
          <p class="text-xs text-zinc-500 mt-0.5">Exibe ponto nos milhares (ex: 1.000,00)</p>
        </div>
        <div class="relative w-9 h-4.5 bg-brand-primary rounded-full shrink-0">
          <span class="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Casas decimais</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">2 casas (0,00)</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Idioma</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Idioma do sistema</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Português (Brasil)</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>
    </div>
  </div>
</template>
