import { Building2, Users, UserCheck, UserCircle } from 'lucide-vue-next';
import type { ClienteStatsData } from '../types/clientes.types';

export const STATS_CONFIG = [
  {
    id: 'total',
    icon: Users,
    label: 'Total de Clientes',
    colorClass: 'bg-zinc-50 text-zinc-900',
    getValue: (stats: ClienteStatsData) => stats.total
  },
  {
    id: 'ativos',
    icon: UserCheck,
    label: 'Clientes Ativos',
    colorClass: 'bg-emerald-50 text-emerald-600',
    getValue: (stats: ClienteStatsData) => stats.ativos
  },
  {
    id: 'pf',
    icon: UserCircle,
    label: 'Pessoa Fisica',
    colorClass: 'bg-blue-50 text-blue-600',
    getValue: (stats: ClienteStatsData) => stats.pf
  },
  {
    id: 'pj',
    icon: Building2,
    label: 'Pessoa Juridica',
    colorClass: 'bg-orange-50 text-orange-600',
    getValue: (stats: ClienteStatsData) => stats.pj
  },
];
