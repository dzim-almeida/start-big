<script setup lang="ts">
const SEPARATOR = '────────────────────────────';
</script>

<template>
  <div class="separator mt-2">{{ SEPARATOR }}</div>
  <div class="text-center mt-1 mb-2">
    <div>{{ new Date().toLocaleString('pt-BR') }}</div>
    <div class="font-bold">SISTEMA STARTBIG</div>
  </div>
</template>
