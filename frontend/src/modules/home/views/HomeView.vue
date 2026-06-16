<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import DashboardFuncionario from '../components/dashboard/DashboardFuncionario.vue';
import DashboardMaster from '../components/dashboard/DashboardMaster.vue';
import { useAuthStore } from '@/shared/stores/auth.store';

const authStore = useAuthStore();
const { userData } = storeToRefs(authStore);

const CARGOS_VISAO_MASTER = ['administrador', 'gerente'];

const isMaster = computed(() => {
  if (userData.value?.is_master) return true;
  const cargo = userData.value?.cargo?.nome?.toLowerCase() ?? '';
  return CARGOS_VISAO_MASTER.some((c) => cargo.includes(c));
});
</script>

<template>
  <DashboardFuncionario v-if="!isMaster" />
  <DashboardMaster v-else />
</template>
