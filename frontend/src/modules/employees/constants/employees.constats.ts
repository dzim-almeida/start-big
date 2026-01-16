import { Users, UserCheck, UserMinus, Clock } from 'lucide-vue-next';

import { TabOption, CardInfo } from '../types/employees.types';

export const TAB_OPTIONS: TabOption[] = [
  { id: 'employee', label: 'Funcionários' },
  { id: 'position', label: 'Cargos' },
];

export const CARDS_INFO: CardInfo[] = [
  { key: 'all_employees', icon: Users, label: 'Total de funcionários' },
  { key: 'actives_now', icon: UserCheck, label: 'Ativos agora' },
  { key: 'in_vacation', icon: Clock, label: 'Em férias' },
  { key: 'left_employees', icon: UserMinus, label: 'Desligados' },
];
