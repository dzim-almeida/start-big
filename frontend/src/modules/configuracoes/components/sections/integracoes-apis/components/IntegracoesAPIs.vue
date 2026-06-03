<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Integrações e APIs</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Conecte o sistema com serviços externos e configure integrações</p>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Nota Fiscal Eletrônica</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Integração NF-e ativa</p>
          <p class="text-xs text-zinc-500 mt-0.5">Emite nota fiscal eletrônica nas vendas</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Ambiente NF-e</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Homologação</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Token de acesso NF-e</label>
        <div class="border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-400 tracking-widest">
          ••••••••••••••••••••
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">PIX</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Integração PIX ativa</p>
          <p class="text-xs text-zinc-500 mt-0.5">Habilita QR Code PIX na finalização da venda</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Chave PIX</label>
        <div class="border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-400">
          Não configurada
        </div>
      </div>
    </div>
  </div>
</template>
