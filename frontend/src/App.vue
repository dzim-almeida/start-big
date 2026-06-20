<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Toaster } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/shared/stores/auth.store';
import { TOKEN_KEY } from '@/api/axios';
import AppLoadingScreen from '@/shared/components/AppLoadingScreen.vue';

const router = useRouter();
const authStore = useAuthStore();
const { isLoading } = storeToRefs(authStore);

function handleBeforeUnload() {
  localStorage.removeItem(TOKEN_KEY);
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload);
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
    <AppLoadingScreen v-if="isLoading || isNavigating" />
    <router-view />
  </div>
</template>