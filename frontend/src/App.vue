<script setup lang="ts">
// import { onBeforeMount } from 'vue';
// import { useRouter } from 'vue-router';
import { Toaster } from 'vue-sonner';
// import { useAuthStore } from './shared/store/auth.store';

// onBeforeMount(async () => {
//   const router = useRouter();
//   const authStore = useAuthStore();

//   if (await authStore.tokenIsSaved()) {
//     router.push({ name: 'home' });
//   }
// });
</script>

<template>
  <div>
    <Toaster position="top-right" :duration="4000" rich-colors close-button />
    <router-view />
  </div>
</template>