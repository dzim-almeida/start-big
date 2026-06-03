<script setup lang="ts">
import { ref, computed } from 'vue';
import { Bell, Menu, Settings } from 'lucide-vue-next';
import { useLayoutStore } from '../../store/layout.store';
import { storeToRefs } from 'pinia';
import SettingsMenu from '../ui/SettingsMenu.vue';

const layoutStore = useLayoutStore();
const { pageTitle, pageSubtitle, isMobile, isSettingsOpen } = storeToRefs(layoutStore);

const settingsButtonRef = ref<HTMLButtonElement | null>(null);

const menuStyle = computed(() => {
  if (!settingsButtonRef.value) return {};
  const rect = settingsButtonRef.value.getBoundingClientRect();
  return {
    top: `${rect.bottom + 8}px`,
    right: `${window.innerWidth - rect.right}px`,
  };
});
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
      <!-- Notifications -->
      <button
        class="relative p-2 text-zinc-500 hover:bg-zinc-100 rounded-lg transition-colors cursor-pointer"
        aria-label="Notificações"
      >
        <Bell :size="20" />
        <span
          class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 border-2 border-white rounded-full"
        ></span>
      </button>

      <!-- Settings Icon -->
      <button
        ref="settingsButtonRef"
        @click="layoutStore.toggleSettings"
        :class="[
          'relative p-2 text-zinc-500 hover:bg-zinc-100 rounded-lg transition-colors cursor-pointer',
          isSettingsOpen && 'bg-zinc-100 text-zinc-800',
        ]"
        aria-label="Configurações"
      >
        <Settings :size="20" />
      </button>
    </div>
  </header>

  <!-- Menu renderizado no body via Teleport para escapar do z-index do header -->
  <Teleport to="body">
    <Transition name="dropdown">
      <SettingsMenu v-if="isSettingsOpen" :style="menuStyle" />
    </Transition>
  </Teleport>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}
</style>
