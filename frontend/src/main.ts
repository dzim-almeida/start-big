import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { vueQueryOptions } from './shared/libs/vueQueryConfig';
import { vMaska } from 'maska/vue';

// import { initStronghold } from './shared/services/secureStorage.service';

import './assets/styles/global.css';
import 'vue-sonner/style.css';

async function startApp() {
  const app = createApp(App);
  const pinia = createPinia();
  app.use(pinia);
  app.use(router);
  app.use(VueQueryPlugin, vueQueryOptions);
  app.directive('maska', vMaska);

//   try {
//     await initStronghold();
//   } catch {
//     console.log('Erro em inciar Secure Storage');
//   }

  app.mount('#app');
}

startApp();
