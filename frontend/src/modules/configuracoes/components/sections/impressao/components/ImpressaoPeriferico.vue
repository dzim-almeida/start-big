<script setup lang="ts">
import { ChevronDown, FileText, Printer } from 'lucide-vue-next'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Impressão e Periféricos</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Configure as impressoras e periféricos conectados ao sistema</p>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Impressora</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Impressora Térmica Ativa</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Daruma DR800 (Térmica - 80mm)</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-xs font-medium text-zinc-600">Largura da Bobina</label>
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col items-center gap-2 p-3 border-2 border-brand-primary rounded-xl bg-brand-primary/5 cursor-pointer">
            <div class="w-3 h-3 rounded-full bg-brand-primary" />
            <FileText :size="22" class="text-zinc-600" />
            <span class="text-xs font-semibold text-zinc-800">Bobina 80mm</span>
          </div>
          <div class="flex flex-col items-center gap-2 p-3 border-2 border-zinc-200 rounded-xl cursor-pointer">
            <div class="w-3 h-3 rounded-full border-2 border-zinc-300" />
            <FileText :size="22" class="text-zinc-400" />
            <span class="text-xs font-medium text-zinc-500">Bobina 58mm</span>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Modo de Impressão</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Texto ESC/POS (Veloz)</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Testar Periféricos</p>

      <BaseButton variant="primary" size="sm" class="w-full" disabled>
        <Printer :size="14" class="mr-2" />
        Imprimir Cupom de Teste
      </BaseButton>

      <div class="flex items-center justify-between py-3 border-t border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Ativar Gaveta de Dinheiro</p>
          <p class="text-xs text-zinc-500 mt-0.5">Abre a gaveta ao finalizar uma venda em dinheiro</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>
    </div>
  </div>
</template>
