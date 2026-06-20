import type { Component } from "vue";

export interface StatsCard {
  key: 'vendas_ativas' | 'vendas_em_orcamento' | 'vendas_finalizadas' | 'vendas_canceladas' | 'ticket_medio';
  icon: Component;
  label: string;
  value: string;
  currency?: boolean;
}