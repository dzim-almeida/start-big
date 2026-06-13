import type { Component } from 'vue';

export interface QuickActionItem {
  id: string;
  icon: Component;
  label: string;
  variant: 'primary' | 'secondary';
  action: () => void;
}

export interface StatCardData {
  id: string;
  icon: Component;
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
}

export type PeriodFilter = 'hoje' | 'semana' | 'mes';
