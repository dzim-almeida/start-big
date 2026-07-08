<template>
  <div class="fixed inset-0 z-9999 flex items-center justify-center bg-white">
    <div class="loading-spinner" />
  </div>
</template>

<style scoped>
.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: var(--color-brand-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
