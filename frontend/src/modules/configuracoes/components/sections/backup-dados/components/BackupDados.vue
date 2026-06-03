<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Backup dos Dados</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Configure e gerencie os backups do banco de dados do sistema</p>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Backup Automático</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Ativar backup automático</p>
          <p class="text-xs text-zinc-500 mt-0.5">Realiza backup nos horários configurados</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Frequência de backup</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Diário</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Horário do backup</label>
        <div class="border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700">
          02:00
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Backup Manual</p>

      <div class="flex flex-col gap-2">
        <BaseButton variant="primary" size="sm" disabled>
          Fazer Backup Agora
        </BaseButton>
        <BaseButton variant="ghost" size="sm" disabled>
          Histórico de Backups
        </BaseButton>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Restauração</p>

      <BaseButton variant="danger" size="sm" disabled>
        Restaurar Backup
      </BaseButton>
    </div>
  </div>
</template>
