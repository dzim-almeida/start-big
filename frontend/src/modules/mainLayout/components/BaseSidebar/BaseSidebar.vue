<script setup lang="ts">
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';

import { useMainLayoutStore } from '@/shared/store/mainLayout.store';
import { useAuthStore } from '@/shared/store/auth.store';

import SidebarItem from './SidebarItem.vue';
import { useSidebar } from '../../composables/useSidebar';
import { ShoppingCart, LogOut } from 'lucide-vue-next';
import { SIDEBAR_SECTIONS } from '@/shared/constants/mainLayout.constants';

const router = useRouter();

const { setActiveTab } = useMainLayoutStore();
const { activeTab } = storeToRefs(useMainLayoutStore());

const { user } = storeToRefs(useAuthStore())

const { isMobile, isMobileOpen } = useSidebar();

const employee = {
  name: 'Gabriel Santos',
  role: 'Gerente de Vendas',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Gabriel',
};

function handleLogout(): void {
  // TODO: Implementar logout real
  router.push({ name: 'login' });
}
</script>

<template>
  <Transition name="slide">
    <aside
      v-show="!isMobile || isMobileOpen"
      :class="[
        'w-72 bg-brand-action text-white flex flex-col h-full border-r border-zinc-800 select-none',
        'transition-transform duration-300 ease-out',
        isMobile ? 'fixed inset-y-0 left-0 z-50' : 'relative',
      ]"
    >
      <!-- Company Header -->
      <div class="p-6">
        <div
          class="flex items-center space-x-3 bg-zinc-900/50 p-3 rounded-2xl border border-zinc-800"
        >
          <div
            class="w-10 h-10 bg-brand-primary rounded-lg flex items-center justify-center shadow-inner"
          >
            <ShoppingCart :size="22" class="text-white" />
          </div>
          <div class="flex-1">
            <h1 class="text-sm font-bold -tracking-normal uppercase -mb-1">BigTec</h1>
            <div class="flex justify-start items-center space-x-1 mt-1">
              <div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
              <span class="text-[10px] text-zinc-500 font-medium">SISTEMA ATIVO</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-4 space-y-4 mt-2 overflow-y-auto">
        <div
          v-for="(section, index) in SIDEBAR_SECTIONS"
          :key="index"
        >
          <p class="px-4 text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-2">
            {{section.title}}
          </p>
          <SidebarItem
            v-for="option in section.options"
            :key="option.id"
            :id="option.id"
            :icon="option.icon"
            :label="option.label"
            :active="activeTab === option.id"
            :route="option.id"
            @click-tab="setActiveTab"
          />
        </div>
      </nav>

      <!-- User Profile -->
      <div class="p-4 mt-auto border-t border-zinc-700/50">
        <div
          class="flex items-center space-x-3 p-3 rounded-2xl bg-zinc-900 hover:bg-zinc-800 transition-colors cursor-pointer group"
        >
          <img
            :src="employee.avatar"
            alt="Foto do usuário"
            class="w-10 h-10 rounded-xl bg-zinc-700 p-0.5"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold truncate group-hover:text-blue-400 transition-colors">
              {{ user?.nome }}
            </p>
            <p class="text-[11px] text-zinc-500 font-medium">{{ user?.cargo }}</p>
          </div>
          <button
            class="p-2 rounded-lg hover:bg-zinc-700 transition-colors group/logout"
            @click.stop="handleLogout"
            aria-label="Sair da conta"
          >
            <LogOut
              :size="16"
              class="text-zinc-600 group-hover/logout:text-red-400 transition-colors"
            />
          </button>
        </div>
      </div>
    </aside>
  </Transition>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease-out;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
