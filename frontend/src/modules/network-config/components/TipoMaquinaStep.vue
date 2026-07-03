<script setup lang="ts">
import { useNetworkConfig } from '../composables/useNetworkConfig'

const { selecionarTipo } = useNetworkConfig()
</script>

<template>
  <div class="space-y-6">
    <div class="text-center space-y-2">
      <h2 class="text-xl font-bold text-gray-800">Como esta máquina irá operar?</h2>
      <p class="text-sm text-gray-500">
        Selecione o papel deste terminal na sua rede local
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <!-- Card Servidor -->
      <button
        class="group flex flex-col items-center gap-3 p-6 rounded-2xl border-2 border-gray-200 bg-white hover:border-brand-primary hover:bg-blue-50/50 transition-all duration-200 cursor-pointer text-center"
        @click="selecionarTipo('servidor')"
      >
        <div class="w-14 h-14 rounded-xl bg-brand-primary/10 flex items-center justify-center group-hover:bg-brand-primary/20 transition-colors">
          <svg class="w-7 h-7 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
          </svg>
        </div>
        <div>
          <h3 class="font-semibold text-gray-800 text-base">Servidor</h3>
          <p class="text-xs text-gray-500 mt-1">
            Este computador gerencia o banco de dados e atende os terminais da rede
          </p>
        </div>
      </button>

      <!-- Card Terminal -->
      <button
        class="group flex flex-col items-center gap-3 p-6 rounded-2xl border-2 border-gray-200 bg-white hover:border-brand-primary hover:bg-blue-50/50 transition-all duration-200 cursor-pointer text-center"
        @click="selecionarTipo('terminal')"
      >
        <div class="w-14 h-14 rounded-xl bg-brand-primary/10 flex items-center justify-center group-hover:bg-brand-primary/20 transition-colors">
          <svg class="w-7 h-7 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25A2.25 2.25 0 015.25 3h13.5A2.25 2.25 0 0121 5.25z" />
          </svg>
        </div>
        <div>
          <h3 class="font-semibold text-gray-800 text-base">Terminal</h3>
          <p class="text-xs text-gray-500 mt-1">
            Conecta-se a um servidor na rede local para acessar o sistema
          </p>
        </div>
      </button>
    </div>
  </div>
</template>
