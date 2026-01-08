<script setup lang="ts">
import { watch } from 'vue';
import { useRoute } from 'vue-router';
import BaseSidebar from '../components/BaseSidebar/BaseSidebar.vue';
import BaseHeader from '../components/BaseHeader.vue';
import { useSidebar } from '../composables/useSidebar';

const route = useRoute();
const { isMobile, isMobileOpen, closeSidebar } = useSidebar();

// Fecha o sidebar quando muda de rota no mobile
watch(
  () => route.path,
  () => {
    if (isMobile.value && isMobileOpen.value) {
      closeSidebar();
    }
  }
);
</script>

<template>
  <div class="flex h-screen bg-brand-off-white overflow-hidden">
    <!-- Overlay Mobile -->
    <Transition name="fade">
      <div
        v-if="isMobile && isMobileOpen"
        class="fixed inset-0 bg-black/50 z-40 lg:hidden"
        @click="closeSidebar"
      />
    </Transition>

    <!-- Sidebar -->
    <BaseSidebar />

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto flex flex-col min-w-0">
      <BaseHeader />
      <div class="flex-1 overflow-y-auto">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
