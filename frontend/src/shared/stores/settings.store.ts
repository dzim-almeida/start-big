import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useSettingsStore = defineStore('settings', () => {
  const isDarkMode = ref<boolean>(false);

  function toggleDarkMode() {
    isDarkMode.value = !isDarkMode.value;
    document.documentElement.classList.toggle('dark', isDarkMode.value);
    localStorage.setItem('bigpdv-dark-mode', String(isDarkMode.value));
  }

  function init() {
    const salvo = localStorage.getItem('bigpdv-dark-mode');
    if (salvo === 'true') {
      isDarkMode.value = true;
      document.documentElement.classList.add('dark');
    }
  }

  return { isDarkMode, toggleDarkMode, init };
});
