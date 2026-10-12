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
    /**
     * Identificador do módulo que esta rota exige (ex.: 'FINANCEIRO').
     * O guard em router/index.ts lê isto e manda para a home quem não tem.
     */
    exigeModulo?: string;
    /**
     * Tela que ocupa a janela inteira (sem sidebar, cabeçalho nem botão de
     * ações rápidas), mas ainda DENTRO do MainLayout: os modais globais (OS,
     * cliente, produto) continuam montados. Ex.: editor de orçamento.
     */
    telaCheia?: boolean;
  }
}
