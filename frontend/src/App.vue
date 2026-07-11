<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Toaster } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/shared/stores/auth.store';
import { useNetworkConfigStore } from '@/shared/stores/networkConfig.store';
import { TOKEN_KEY } from '@/api/axios';
import { getDesconectarUrl } from '@/shared/services/licenca.service';
import { aguardarBackend, verificarSaude } from '@/shared/services/system/health.service';
import { tauriDisponivel, getConfig, setRoleClient } from '@/shared/services/system/tauriConfig.service';
import { reinitBackendUrl } from '@/api/backendUrl';
import { tentarAutoDiscovery } from '@/modules/network-config/composables/useAutoDiscovery';
import AppLoadingScreen from '@/shared/components/AppLoadingScreen.vue';
import { useHealthMonitor } from '@/shared/composables/useHealthMonitor';

// sessionStorage persiste em reloads mas é limpo ao fechar a janela.
// DEVE rodar ANTES de useAuthStore() para que useUserQuery() veja o token já removido.
const SESSION_KEY = 'session_active';
if (!sessionStorage.getItem(SESSION_KEY)) {
  localStorage.removeItem(TOKEN_KEY);
}
sessionStorage.setItem(SESSION_KEY, 'true');

const router = useRouter();
const authStore = useAuthStore();
const networkStore = useNetworkConfigStore();
const { isLoading } = storeToRefs(authStore);

const appReady = ref(false);

useHealthMonitor(appReady);

function handleBeforeUnload() {
  navigator.sendBeacon(getDesconectarUrl());
}

onMounted(async () => {
  window.addEventListener('beforeunload', handleBeforeUnload);

  if (tauriDisponivel()) {
    const config = await getConfig();

    if (!config.configured) {
      networkStore.setNecessitaConfiguracao(true);
      router.replace({ name: 'network-config' });
    } else {
      const healthy = await aguardarBackend(config.is_server);
      if (!healthy) {
        if (!config.is_server) {
          // Terminal: tenta auto-discovery antes de mostrar tela de erro
          const servidor = await tentarAutoDiscovery();
          if (servidor) {
            await setRoleClient(servidor.ip, servidor.port);
            await reinitBackendUrl();
            const retryOk = await verificarSaude(5000);
            if (retryOk) {
              appReady.value = true;
              return;
            }
            networkStore.setConfigAtual(servidor.ip, servidor.port);
          } else {
            networkStore.setConfigAtual(config.server_ip, config.server_port);
          }
          networkStore.setErroConexaoTerminal(true);
          router.replace({ name: 'erro-conexao' });
        } else {
          // Servidor: wizard completo (sidecar local falhou)
          networkStore.setNecessitaConfiguracao(true);
          router.replace({ name: 'network-config' });
        }
      }
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
