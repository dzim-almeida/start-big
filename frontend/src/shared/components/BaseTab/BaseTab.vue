<script setup lang="ts">
/**
 * @component BaseTab
 * @description Componente de abas reutilizável que permite alternar entre
 * diferentes seções de conteúdo. Suporta estilização customizada para o estado ativo.
 */

interface Tab {
  id: string;
  label: string;
}

interface TabProps {
  tabs: Tab[];
}

const props = defineProps<TabProps>();

const activeTab = defineModel<string>({ required: true });

function selectTab(tabId: string) {
  activeTab.value = tabId;
}
</script>

<template>
  <div class="inline-flex gap-3 overflow-hidden">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="relative p-1 text-md transition-colors duration-200 cursor-pointer focus:outline-none"
      :class="[
        activeTab === tab.id
          ? 'text-brand-action font-bold border-b-2 border-brand-primary'
          : 'text-gray-400 font-medium hover:text-brand-action',
      ]"
      @click="selectTab(tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
