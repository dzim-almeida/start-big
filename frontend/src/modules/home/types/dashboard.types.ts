import type { Component } from 'vue';

export interface StatCardData {
  id: string;
  icon: Component;
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
}

export interface Transaction {
  id: string;
  customer: string;
  value: string;
  status: 'completed' | 'pending' | 'cancelled';
}

export interface QuickActionItem {
  id: string;
  icon: Component;
  label: string;
  variant: 'primary' | 'secondary';
}

export type PeriodFilter = 'today' | 'week' | 'month';

export interface DashboardData {
  stats: StatCardData[];
  transactions: Transaction[];
  quickActions: QuickActionItem[];
  lowStockCount: number;
}
