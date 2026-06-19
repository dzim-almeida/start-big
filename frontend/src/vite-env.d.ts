/// <reference types="vite/client" />

import 'vue-router';

declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

declare module '*.png' {
  const src: string;
  export default src;
}

declare module '*.jpg' {
  const src: string;
  export default src;
}

declare module '*.svg' {
  const src: string;
  export default src;
}

declare module 'vue-router' {
  interface RouteMeta {
    title?: string;
    subtitle?: string;
    tabId?: string;
    requiresAuth?: boolean;
  }
}
