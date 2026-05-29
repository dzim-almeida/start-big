import { FeaturesOptions } from '../types/onboarding.types';

import { 
    ChartLine,
    ClockArrowUp,
    ShieldCheck
} from 'lucide-vue-next'

export const FEATURES_OPTIONS: FeaturesOptions[] = [
  {
    icon: ChartLine,
    title: 'Gestão Inteligente',
    description: 'Controle completo do seu negócio em um só lugar',
  },
  {
    icon: ClockArrowUp,
    title: 'Economia de Tempo',
    description: 'Automatize processos e foque no que importa',
  },
  {
    icon: ShieldCheck,
    title: 'Segurança Total',
    description: 'Seus dados protegidos com tecnologia de ponta',
  },
];
