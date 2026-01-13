// .storybook/preview.ts
import type { Preview } from "@storybook/vue3";
import { setup } from "@storybook/vue3";
import { createPinia } from "pinia";
import '../src/assets/styles/global.css';
// Se usar PrimeVue, descomente abaixo:
// import PrimeVue from 'primevue/config';

setup((app) => {
  app.use(createPinia());
  // app.use(PrimeVue);
});

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
};

export default preview;