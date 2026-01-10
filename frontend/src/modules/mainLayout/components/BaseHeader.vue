<script setup lang="ts">
import { Bell, Search, Menu } from 'lucide-vue-next';
import { useLayoutStore } from '../store/layout.store';
import { storeToRefs } from 'pinia';

const layoutStore = useLayoutStore();
const {
  pageTitle,
  pageSubtitle,
  isMobile,
} = storeToRefs(layoutStore);
</script>

<template>
  <header
    class="w-full h-16 md:h-20 bg-white border-b border-zinc-200 px-4 md:px-8 flex items-center justify-between sticky top-0 z-30"
  >
    <!-- Left Section: Hamburger + Title -->
    <div class="flex items-center gap-3 md:gap-4">
      <!-- Hamburger Menu (Mobile Only) -->
      <button
        v-if="isMobile"
        class="p-2 -ml-2 text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
        @click="layoutStore.toggleSidebar"
        aria-label="Abrir menu"
      >
        <Menu :size="24" />
      </button>

      <!-- Page Title -->
      <div class="flex flex-col">
        <h1 class="text-lg md:text-2xl text-brand-primary font-extrabold leading-tight">
          {{ pageTitle }}
        </h1>
        <p class="text-[10px] md:text-xs text-zinc-400 font-medium hidden sm:block">
          {{ pageSubtitle }}
        </p>
      </div>
    </div>

    <!-- Right Section: Actions -->
    <div class="flex flex-1 items-center justify-end xl:max-w-2xl lg:max-w-md gap-2 md:gap-4">
      <!-- Center Section: Search (Hidden on small mobile) -->
      <div class="hidden md:flex flex-1 justify-center mx-4">
        <div class="relative w-full">
          <Search
            class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none"
            :size="18"
          />
          <input
            type="text"
            placeholder="Buscar produtos, vendas ou clientes..."
            class="w-full bg-zinc-100 border-none rounded-xl py-2.5 pl-10 pr-4 text-sm focus:ring-2 focus:ring-brand-primary/30 focus:bg-white transition-all outline-none placeholder:text-zinc-400"
          />
        </div>
      </div>

      <!-- Search Icon (Mobile) -->
      <button
        class="md:hidden p-2 text-zinc-500 hover:bg-zinc-100 rounded-lg transition-colors"
        aria-label="Buscar"
      >
        <Search :size="20" />
      </button>

      <!-- Notifications -->
      <button
        class="relative p-2 text-zinc-500 hover:bg-zinc-100 rounded-lg transition-colors"
        aria-label="Notificações"
      >
        <Bell :size="20" />
        <span
          class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 border-2 border-white rounded-full"
        ></span>
      </button>
    </div>
  </header>
</template>
