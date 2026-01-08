import { ref, computed, onMounted, onUnmounted } from 'vue';

const isMobileOpen = ref(true);
const isMobile = ref(false);

const MOBILE_BREAKPOINT = 768;

function checkIsMobile(): void {
  isMobile.value = window.innerWidth < MOBILE_BREAKPOINT;

  // Fecha sidebar automaticamente quando redimensiona para desktop
  if (!isMobile.value && isMobileOpen.value) {
    isMobileOpen.value = false;
  }
}

export function useSidebar() {
  const isOpen = computed(() => !isMobile.value || isMobileOpen.value);

  function openSidebar(): void {
    if (isMobile.value) {
      isMobileOpen.value = true;
    }
  }

  function closeSidebar(): void {
    isMobileOpen.value = false;
  }

  function toggleSidebar(): void {
    if (isMobile.value) {
      isMobileOpen.value = !isMobileOpen.value;
    }
  }

  function setupResizeListener(): void {
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
  }

  function cleanupResizeListener(): void {
    window.removeEventListener('resize', checkIsMobile);
  }

  onMounted(() => {
    setupResizeListener();
  });

  onUnmounted(() => {
    cleanupResizeListener();
  });

  return {
    isMobile,
    isMobileOpen,
    isOpen,
    openSidebar,
    closeSidebar,
    toggleSidebar,
    setupResizeListener,
    cleanupResizeListener,
  };
}
