<script setup lang="ts">
defineProps<{
  leftLabel: string;
  rightLabel: string;
  rightName?: string;
}>();

const SEPARATOR = '────────────────────────────';
</script>

<template>
  <div class="separator" style="margin-top: 32px;">{{ SEPARATOR }}</div>
  <div class="section" style="margin-top: 28px;">
    <div class="signature-line"></div>
    <div class="text-center font-bold">{{ leftLabel }}</div>
  </div>
  <div class="section" style="margin-top: 32px;">
    <div class="signature-line"></div>
    <div class="text-center font-bold">{{ rightLabel }}</div>
    <div v-if="rightName" class="text-center">{{ rightName }}</div>
  </div>
</template>
