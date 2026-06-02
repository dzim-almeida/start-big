<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Ordens de Serviço</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Configure os padrões e fluxos das ordens de serviço</p>
    </div>

    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Prazos</p>

      <div class="py-3 border-b border-zinc-100">
        <label class="text-xs font-medium text-zinc-600">Prazo padrão de entrega (dias)</label>
        <div class="mt-1.5 border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700">
          7
        </div>
      </div>
    </div>

    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Notificações</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Notificar cliente ao criar OS</p>
          <p class="text-xs text-zinc-500 mt-0.5">Envia mensagem automática ao abrir a ordem</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Notificar cliente ao concluir OS</p>
          <p class="text-xs text-zinc-500 mt-0.5">Envia mensagem automática ao finalizar</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Fluxo</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Status inicial padrão</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Em Aberto</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-t border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir aprovação do cliente</p>
          <p class="text-xs text-zinc-500 mt-0.5">Cliente deve aprovar o orçamento antes de iniciar</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>
    </div>
  </div>
</template>
