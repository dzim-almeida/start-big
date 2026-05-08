import type { Component } from "vue";

export interface StatsCard {
  key: 'vendas_em_aberto' | 'vendas_finalizadas' | 'vendas_canceladas' | 'ticket_medio';
  icon: Component;
  label: string;
  value: string;
  currency?: boolean;
}