/**
 * @fileoverview Constants for employees module
 * @description Tab options and stats card configuration
 */

import { Users, UserCheck, UserMinus, Clock } from 'lucide-vue-next';

import type { TabOption, CardInfo } from '../types/employees.types';

export const TAB_OPTIONS: TabOption[] = [
  { id: 'employee', label: 'Funcionarios' },
  { id: 'position', label: 'Cargos' },
];

export const CARDS_INFO: CardInfo[] = [
  { key: 'all_employees', icon: Users, label: 'Total de funcionarios' },
  { key: 'actives_now', icon: UserCheck, label: 'Ativos agora' },
  { key: 'in_vacation', icon: Clock, label: 'Em ferias' },
  { key: 'left_employees', icon: UserMinus, label: 'Desligados' },
];
