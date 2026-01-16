import type { Component } from 'vue';

export interface TabOption {
  id: 'employee' | 'position';
  label: string;
}

export interface StatsDada {
  total_funcionarios: number;
  ativos_agora: number;
  em_ferias: number;
  desligados: number;
}

export type StatsKeys = 
    | 'actives_now'
    | 'all_employees'
    | 'in_vacation'
    | 'left_employees'

export interface CardInfo {
  key: StatsKeys; 
  icon: Component;
  label: string;
}

export interface Employee {
  id: number;
  name: string;
  email: string;
  role: string;          
  status: 'active' | 'vacation' | 'inactive';
  avatarUrl?: string; 
}
