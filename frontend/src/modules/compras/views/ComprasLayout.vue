<script setup lang="ts">
/**
 * Casca do módulo de Compras — mesmo papel do FinanceiroLayout.
 *
 * Não decide acesso: módulo e permissão já foram conferidos no `beforeEach` do
 * router (`exigeModulo`) e no backend, que recusa a rota com 403.
 */
</script>

<template>
  <div class="h-full flex flex-col p-4 md:p-6 lg:p-8 overflow-y-auto">
    <router-view />
  </div>
</template>
