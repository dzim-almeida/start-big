import { VueQueryPluginOptions } from "@tanstack/vue-query";

export const vueQueryOptions: VueQueryPluginOptions = {
  queryClientConfig: {
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false, // Evita requisições ao trocar de aba
        retry: 1, // Tenta novamente 1 vez se der erro, antes de falhar
        staleTime: 1000 * 60 * 5, // Dados são considerados "frescos" por 5 minutos (cache)
      },
    },
  },
}