import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import { RouteLocationNormalized, useRoute } from 'vue-router';

import { SidebarLabelOptions } from '../types/layout.types';

export const useLayoutStore = defineStore('layout', () => {
  //Constantes
  const MOBILE_BREAKPOINT = 768;

  //Utilitarios
  const route = useRoute();

  //Menu mobile
  const isMobileOpen = ref(false);
  const isMobile = ref(false);

  const isOpen = computed(() => !isMobile.value || isMobileOpen.value);

  function checkIsMobile(): void {
    isMobile.value = window.innerWidth < MOBILE_BREAKPOINT;

    if (!isMobile.value && isMobileOpen.value) {
      isMobileOpen.value = false;
    }
  }

  //Menu geral
  const pageTitle = ref<SidebarLabelOptions>('Início');
  const pageSubtitle = ref<string>('');
  const activeTab = ref<string>('');
  
  const isQuickOpen = ref<boolean>(false);

  //Listener
  function init() {
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
  }

  function close() {
    window.removeEventListener('resize', checkIsMobile);
  }

   //Metodos
  function updatePageInfo(route: RouteLocationNormalized) {
    const { meta } = route;
    pageTitle.value = meta.title as SidebarLabelOptions;
    pageSubtitle.value = meta.subtitle || '';
    activeTab.value = meta.tabId || '';
  }

  function closeSidebar() {
    isMobileOpen.value = false;
  }

  function toggleSidebar() {
    if (isMobile) {
      isMobileOpen.value = !isMobileOpen.value;
    }
  }

  function toggleQuick() {
    isQuickOpen.value = !isQuickOpen.value
  }

  watch(
    () => route.path,
    () => {
      if (isMobile.value && isMobileOpen.value) {
        closeSidebar();
      }
    },
  );

  return {
    // Refs
    pageTitle,
    pageSubtitle,
    activeTab,
    isMobile,
    isMobileOpen,
    isOpen,
    isQuickOpen,

    //Metodos
    updatePageInfo,
    toggleSidebar,
    closeSidebar,
    toggleQuick,

    // Listeners
    init,
    close,
  };
});
