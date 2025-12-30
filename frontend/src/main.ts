import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { vueQueryOptions } from './shared/libs/vueQueryConfig';
import { vMaska } from 'maska/vue';

import './assets/styles/global.css';
import 'vue-sonner/style.css';

const app = createApp(App);
app.use(router);
app.use(VueQueryPlugin, vueQueryOptions);
app.directive('maska', vMaska)
app.mount('#app');
