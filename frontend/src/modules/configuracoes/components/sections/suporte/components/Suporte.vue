<script setup lang="ts">
import { Headphones, BookOpen, HelpCircle } from 'lucide-vue-next'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Suporte e Ajuda</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Encontre ajuda, entre em contato com o suporte e acesse recursos</p>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Contato</p>

      <div class="flex flex-col gap-2">
        <BaseButton variant="primary" size="sm" disabled>
          <Headphones :size="14" class="mr-2" />
          Falar com Suporte
        </BaseButton>
        <BaseButton variant="ghost" size="sm" disabled>
          <HelpCircle :size="14" class="mr-2" />
          Central de Ajuda
        </BaseButton>
        <BaseButton variant="ghost" size="sm" disabled>
          <BookOpen :size="14" class="mr-2" />
          Tutoriais em Vídeo
        </BaseButton>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Acesso Remoto</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Ativar acesso remoto</p>
          <p class="text-xs text-zinc-500 mt-0.5">Permite que o suporte acesse o sistema remotamente</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Código de acesso</label>
        <div class="border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-400 tracking-widest">
          ••••••••
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Informações do Sistema</p>

      <div class="bg-zinc-50 rounded-xl p-4 flex flex-col gap-2.5">
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Versão do sistema</span>
          <span class="text-xs font-semibold text-zinc-700">1.0.0</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Última atualização</span>
          <span class="text-xs font-semibold text-zinc-700">01/06/2026</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Ambiente</span>
          <span class="text-xs font-semibold text-emerald-600">Produção</span>
        </div>
      </div>
    </div>
  </div>
</template>
