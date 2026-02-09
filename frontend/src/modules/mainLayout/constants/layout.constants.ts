import {
  ShoppingCart,
  LayoutDashboard,
  Tags,
  Users,
  BookOpen,
  Building,
  IdCard,
  Wrench,
} from 'lucide-vue-next';

import { SidebarSection } from '../types/layout.types';
import { PERMISSIONS } from '@/shared/constants/permissions.constants';

export const SIDEBAR_SECTIONS: SidebarSection[] = [
  {
    title: 'MENU PRINCIPAL',
    options: [
      {
        id: 'home',
        icon: LayoutDashboard,
        label: 'Início',
        requiredPermission: PERMISSIONS.dashboard,
      },
      {
        id: 'sales',
        icon: ShoppingCart,
        label: 'Vendas',
        requiredPermission: PERMISSIONS.sales,
      },
      {
        id: 'services',
        icon: Wrench,
        label: 'Serviços',
        requiredPermission: PERMISSIONS.services,
      },
      {
        id: 'customers',
        icon: Users,
        label: 'Clientes',
        requiredPermission: PERMISSIONS.customers,
      },
      {
        id: 'products',
        icon: Tags,
        label: 'Produtos',
        requiredPermission: PERMISSIONS.products,
      },
      {
        id: 'catalog',
        icon: BookOpen,
        label: 'Catálogo',
        requiredPermission: PERMISSIONS.catalog,
      },
    ],
  },
  {
    title: 'EMPRESA',
    options: [
      {
        id: 'enterprise',
        icon: Building,
        label: 'Dados da Empresa',
        requiredPermission: PERMISSIONS.enterprise,
      },
      {
        id: 'employees',
        icon: IdCard,
        label: 'Gestão de Equipe',
        requiredPermission: PERMISSIONS.employees,
      },
    ],
  },
] as const;
