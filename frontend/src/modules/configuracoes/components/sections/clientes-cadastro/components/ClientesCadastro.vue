<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Clientes e Cadastro</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Defina os campos obrigatórios e padrões no cadastro de clientes</p>
    </div>

    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Campos Obrigatórios</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir CPF no cadastro</p>
          <p class="text-xs text-zinc-500 mt-0.5">CPF se torna campo obrigatório</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir endereço no cadastro</p>
          <p class="text-xs text-zinc-500 mt-0.5">Endereço se torna campo obrigatório</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir telefone no cadastro</p>
          <p class="text-xs text-zinc-500 mt-0.5">Telefone se torna campo obrigatório</p>
        </div>
        <div class="relative w-9 h-4.5 bg-brand-primary rounded-full shrink-0">
          <span class="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Padrões</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Tipo de pessoa padrão</label>
        <div class="flex items-center justify-between border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50">
          <span class="text-sm text-zinc-700">Pessoa Física</span>
          <ChevronDown :size="14" class="text-zinc-400 shrink-0" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-t border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir duplicidade de CPF</p>
          <p class="text-xs text-zinc-500 mt-0.5">Permite cadastrar dois clientes com o mesmo CPF</p>
        </div>
        <div class="relative w-9 h-4.5 bg-zinc-200 rounded-full shrink-0">
          <span class="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow" />
        </div>
      </div>
    </div>
  </div>
</template>
