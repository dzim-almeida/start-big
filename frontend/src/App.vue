<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Toaster } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/shared/stores/auth.store';
import { useNetworkConfigStore } from '@/shared/stores/networkConfig.store';
import { TOKEN_KEY } from '@/api/axios';
import { verificarSaude } from '@/shared/services/system/health.service';
import { tauriDisponivel } from '@/shared/services/system/tauriConfig.service';
import AppLoadingScreen from '@/shared/components/AppLoadingScreen.vue';

const router = useRouter();
const authStore = useAuthStore();
const networkStore = useNetworkConfigStore();
const { isLoading } = storeToRefs(authStore);

const appReady = ref(false);

function handleBeforeUnload() {
  localStorage.removeItem(TOKEN_KEY);
}

onMounted(async () => {
  window.addEventListener('beforeunload', handleBeforeUnload);

  if (tauriDisponivel()) {
    const healthy = await verificarSaude();
    if (!healthy) {
      networkStore.setNecessitaConfiguracao(true);
      router.replace({ name: 'network-config' });
    }
  }

  appReady.value = true;
});

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload);
});

const isNavigating = ref(false);

router.beforeEach(() => {
  isNavigating.value = true;
});

router.afterEach(() => {
  isNavigating.value = false;
});
</script>

<template>
  <div>
    <Toaster position="top-right" :duration="4000" rich-colors close-button />
    <AppLoadingScreen v-if="!appReady || isLoading || isNavigating" />
    <router-view v-if="appReady" />
  </div>
</template>