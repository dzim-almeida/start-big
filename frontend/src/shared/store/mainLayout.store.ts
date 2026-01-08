import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { sidebarLabelOptions } from '../types/mainLayout.types';

export const useMainLayoutStore = defineStore('mainLayout', () => {
    const router = useRouter()
    const pageTitle = ref<sidebarLabelOptions>('Início');
    const activeTab = ref<string>('home');

    function setActiveTab(id: string, title: sidebarLabelOptions, route: string) {
        pageTitle.value = title;
        activeTab.value = id;
        router.push({ name: route })
    }

    return {
        // Refs
        pageTitle,
        activeTab,

        // Metodos
        setActiveTab,
    }
    
});
