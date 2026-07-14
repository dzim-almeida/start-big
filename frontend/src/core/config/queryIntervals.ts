// Intervalos de polling (refetchInterval) para sincronização entre terminais na rede local.
// Queries com refetchInterval fazem re-fetch automático mesmo sem interação do usuário,
// garantindo que dados alterados em um terminal sejam visíveis nos demais.

export const REFETCH_REALTIME = 1000 * 10      // 5s  - vendas, OS, orçamento
export const REFETCH_DASHBOARD = 1000 * 30     // 30s - dashboard
export const REFETCH_CADASTROS = 1000 * 60 * 2 // 2min - clientes, produtos, funcionários, etc
export const REFETCH_CONFIG = 1000 * 60 * 5    // 5min - configurações do sistema
