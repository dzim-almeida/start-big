<script setup lang="ts">
import { Toaster } from 'vue-sonner';
</script>

<template>
  <div>
    <Toaster
      position="top-right"
      :duration="4000"
      rich-colors
      close-button
    />
    <router-view />
  </div>
</template>