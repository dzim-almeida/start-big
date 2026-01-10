<script setup lang="ts">
import { Zap } from 'lucide-vue-next';
import { useMagicKeys, whenever } from '@vueuse/core'

import BaseSidebar from '../components/BaseSidebar/BaseSidebar.vue';
import BaseHeader from '../components/BaseHeader.vue';
import QuickActions from '../components/commons/QuickActions.vue';

import { useDashboard } from '@/modules/home/composables/useDashboard';
import { useLayoutStore } from '../store/layout.store';
import { storeToRefs } from 'pinia';

const layoutStore = useLayoutStore();
const { isMobile, isMobileOpen, isQuickOpen } = storeToRefs(layoutStore);

const { quickActions, lowStockCount } = useDashboard()

const { Ctrl_K } = useMagicKeys();

whenever(Ctrl_K, () => {
  layoutStore.toggleQuick();
});

</script>

<template>
  <div class="flex h-screen bg-brand-off-white overflow-hidden">
    <Transition name="fade">
      <div
        v-if="(isMobile && isMobileOpen)"
        class="fixed inset-0 bg-black/50 z-40 lg:hidden"
        @click="layoutStore.closeSidebar"
      />
    </Transition>

      <div
        v-if="isQuickOpen"
        class="fixed inset-0 bg-transparent z-40"
        @click="layoutStore.toggleQuick"
      />

    <BaseSidebar />

    <main class="relative flex-1 overflow-y-auto flex flex-col min-w-0">
      <BaseHeader />
      <div class="flex-1 overflow-y-auto">
        <router-view />
      </div>

      <Transition name="pop" mode="out-in">
        <button
          v-if="!isQuickOpen"
          class="fixed z-10 right-8 bottom-8 text-white bg-brand-primary p-3 rounded-full cursor-pointer shadow-lg hover:bg-brand-primary/90 transition-colors"
          @click="layoutStore.toggleQuick"
        >
          <Zap :size="24" fill="white" />
        </button>
        
        <div v-else class="fixed bottom-8 right-8 z-50">
          <QuickActions @clicked="layoutStore.toggleQuick" :actions="quickActions" :low-stock-count="lowStockCount" />
        </div>
      </Transition>

    </main>
  </div>
</template>

<style scoped>
/* Transição existente do Overlay */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* --- NOVA TRANSIÇÃO: Quick Actions (Efeito Pop/Scale) --- */
.pop-enter-active,
.pop-leave-active {
  /* O cubic-bezier dá um efeito de elástico/salto sutil */
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: scale(0.5); /* Começa/Termina pequeno */
}
</style>