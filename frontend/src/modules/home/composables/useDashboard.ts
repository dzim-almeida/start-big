import { ref, computed } from 'vue';
import { TrendingUp, Wrench, Users, CreditCard } from 'lucide-vue-next';

import { formatCurrency, formatVariacao } from '@/shared/utils/finance';
import { useDashboardStatsQuery } from './queries/useDashboardStatsQuery';
import { useOSVencendoQuery } from './queries/useOSVencendoQuery';
import { useEstoqueBaixoQuery } from './queries/useEstoqueBaixoQuery';
import { useUltimasVendasQuery } from './queries/useUltimasVendasQuery';

import type { StatCardData, PeriodFilter } from '../types/dashboard.types';

const PERIOD_LABELS: Record<PeriodFilter, string> = {
  hoje: 'hoje',
  semana: 'esta semana',
  mes: 'este mês',
};

export function useDashboard() {
  const activePeriod = ref<PeriodFilter>('hoje');

  // Queries
  const statsQuery = useDashboardStatsQuery(activePeriod);
  const osVencendoQuery = useOSVencendoQuery();
  const estoqueBaixoQuery = useEstoqueBaixoQuery();
  const ultimasVendasQuery = useUltimasVendasQuery();

  // Stats cards computados a partir dos dados da API
  const stats = computed<StatCardData[]>(() => {
    const data = statsQuery.data.value;
    if (!data) return [];

    return [
      {
        id: 'vendas-totais',
        icon: TrendingUp,
        label: 'Vendas Totais',
        value: formatCurrency(data.vendas_total),
        change: formatVariacao(data.vendas_total_variacao),
        isPositive: data.vendas_total_variacao >= 0,
      },
      {
        id: 'ordens-servico',
        icon: Wrench,
        label: 'Ordens de Serviço',
        value: String(data.os_count),
        change: formatVariacao(data.os_count_variacao),
        isPositive: data.os_count_variacao >= 0,
      },
      {
        id: 'novos-clientes',
        icon: Users,
        label: 'Novos Clientes',
        value: String(data.novos_clientes),
        change: formatVariacao(data.novos_clientes_variacao),
        isPositive: data.novos_clientes_variacao >= 0,
      },
      {
        id: 'ticket-medio',
        icon: CreditCard,
        label: 'Ticket Médio',
        value: formatCurrency(data.ticket_medio),
        change: formatVariacao(data.ticket_medio_variacao),
        isPositive: data.ticket_medio_variacao >= 0,
      },
    ];
  });

  const osVencendo = computed(() => osVencendoQuery.data.value?.items ?? []);
  const estoqueBaixo = computed(() => estoqueBaixoQuery.data.value?.items ?? []);
  const ultimasVendas = computed(() => ultimasVendasQuery.data.value?.items ?? []);

  const periodDescription = computed(
    () => `Confira os resultados da loja para ${PERIOD_LABELS[activePeriod.value]}.`,
  );

  function setPeriod(period: PeriodFilter): void {
    activePeriod.value = period;
  }

  return {
    activePeriod,
    stats,
    setPeriod,
    periodDescription,
    osVencendo,
    estoqueBaixo,
    ultimasVendas,
    isLoadingStats: statsQuery.isLoading,
    isLoadingOS: osVencendoQuery.isLoading,
    isLoadingEstoque: estoqueBaixoQuery.isLoading,
    isLoadingVendas: ultimasVendasQuery.isLoading,
    isErrorStats: statsQuery.isError,
    isErrorOS: osVencendoQuery.isError,
    isErrorEstoque: estoqueBaixoQuery.isError,
    isErrorVendas: ultimasVendasQuery.isError,
  };
}
