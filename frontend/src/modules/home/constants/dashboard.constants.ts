export const dashboardKeys = {
  all: ['dashboard'] as const,
  stats: (periodo: string) => [...dashboardKeys.all, 'stats', periodo] as const,
  osVencendo: () => [...dashboardKeys.all, 'os-vencendo'] as const,
  estoqueBaixo: () => [...dashboardKeys.all, 'estoque-baixo'] as const,
  ultimasVendas: () => [...dashboardKeys.all, 'ultimas-vendas'] as const,
};

export const DASHBOARD_STALE_TIME = 1000 * 60;
