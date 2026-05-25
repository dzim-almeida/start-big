import { ref, computed } from 'vue';
import { TrendingUp, ShoppingCart, Users, CreditCard, Plus, BarChart3 } from 'lucide-vue-next';
import type { StatCardData, Transaction, QuickActionItem, PeriodFilter } from '../types/dashboard.types';

// Dados mockados das estatísticas por período
const mockStatsByPeriod: Record<PeriodFilter, StatCardData[]> = {
  today: [
    {
      id: 'total-sales',
      icon: TrendingUp,
      label: 'Vendas Totais',
      value: 'R$ 12.450,00',
      change: '+12.5%',
      isPositive: true,
    },
    {
      id: 'orders',
      icon: ShoppingCart,
      label: 'Pedidos Realizados',
      value: '48',
      change: '+5.2%',
      isPositive: true,
    },
    {
      id: 'new-customers',
      icon: Users,
      label: 'Novos Clientes',
      value: '12',
      change: '-2.4%',
      isPositive: false,
    },
    {
      id: 'avg-ticket',
      icon: CreditCard,
      label: 'Ticket Médio',
      value: 'R$ 259,37',
      change: '+0.8%',
      isPositive: true,
    },
  ],
  week: [
    {
      id: 'total-sales',
      icon: TrendingUp,
      label: 'Vendas Totais',
      value: 'R$ 87.150,00',
      change: '+18.3%',
      isPositive: true,
    },
    {
      id: 'orders',
      icon: ShoppingCart,
      label: 'Pedidos Realizados',
      value: '336',
      change: '+12.1%',
      isPositive: true,
    },
    {
      id: 'new-customers',
      icon: Users,
      label: 'Novos Clientes',
      value: '84',
      change: '+8.7%',
      isPositive: true,
    },
    {
      id: 'avg-ticket',
      icon: CreditCard,
      label: 'Ticket Médio',
      value: 'R$ 259,37',
      change: '+3.2%',
      isPositive: true,
    },
  ],
  month: [
    {
      id: 'total-sales',
      icon: TrendingUp,
      label: 'Vendas Totais',
      value: 'R$ 348.600,00',
      change: '+22.1%',
      isPositive: true,
    },
    {
      id: 'orders',
      icon: ShoppingCart,
      label: 'Pedidos Realizados',
      value: '1.344',
      change: '+15.8%',
      isPositive: true,
    },
    {
      id: 'new-customers',
      icon: Users,
      label: 'Novos Clientes',
      value: '336',
      change: '+11.2%',
      isPositive: true,
    },
    {
      id: 'avg-ticket',
      icon: CreditCard,
      label: 'Ticket Médio',
      value: 'R$ 259,37',
      change: '+5.4%',
      isPositive: true,
    },
  ],
};

// Dados mockados das transações recentes
const mockTransactions: Transaction[] = [
  { id: '#8821', customer: 'Ana Paula Mendes', value: 'R$ 450,00', status: 'completed' },
  { id: '#8820', customer: 'Marcos Vinícius', value: 'R$ 120,50', status: 'pending' },
  { id: '#8819', customer: 'Julia Oliveira', value: 'R$ 1.200,00', status: 'completed' },
  { id: '#8818', customer: 'Rodrigo Silva', value: 'R$ 89,90', status: 'completed' },
  { id: '#8817', customer: 'Fernanda Costa', value: 'R$ 567,80', status: 'pending' },
];

// Dados mockados das ações rápidas
const mockQuickActions: QuickActionItem[] = [
  { id: 'new-product', icon: Plus, label: 'Novo Produto', variant: 'primary' },
  { id: 'new-customer', icon: Users, label: 'Cadastrar Cliente', variant: 'secondary' },
  { id: 'daily-report', icon: BarChart3, label: 'Relatório Diário', variant: 'secondary' },
];

export function useDashboard() {
  const activePeriod = ref<PeriodFilter>('today');
  const lowStockCount = ref(5);

  const stats = computed(() => mockStatsByPeriod[activePeriod.value]);

  const transactions = computed(() => mockTransactions);

  const quickActions = computed(() => mockQuickActions);

  function setPeriod(period: PeriodFilter): void {
    activePeriod.value = period;
  }

  // Nome do período para exibição
  const periodLabels: Record<PeriodFilter, string> = {
    today: 'Hoje',
    week: 'Semana',
    month: 'Mês',
  };

  const periodLabel = computed(() => periodLabels[activePeriod.value]);

  return {
    activePeriod,
    stats,
    transactions,
    quickActions,
    lowStockCount,
    setPeriod,
    periodLabel,
  };
}
