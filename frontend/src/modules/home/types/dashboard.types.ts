import type { Component } from 'vue';

export interface StatCardData {
  id: string;
  icon: Component;
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
}

export type PeriodFilter = 'hoje' | 'semana' | 'mes';
