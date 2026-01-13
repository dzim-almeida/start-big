import {
  ShoppingCart,
  LayoutDashboard,
  Package,
  Tags,
  Users,
  BookOpen,
  Building,
  IdCard,
  Wrench,
} from 'lucide-vue-next';

import { SidebarSection } from '../types/layout.types';

export const SIDEBAR_SECTIONS: SidebarSection[] = [
  {
    title: 'MENU PRINCIPAL',
    options: [
      {
        id: 'home',
        icon: LayoutDashboard,
        label: 'Início',
        requiredPermission: 'view_dashboard',
      },
      {
        id: 'sales',
        icon: ShoppingCart,
        label: 'Vendas',
        requiredPermission: 'view_sales',
      },
      {
        id: 'storage',
        icon: Package,
        label: 'Estoque',
        requiredPermission: 'view_storage',
      },
      {
        id: 'services',
        icon: Wrench,
        label: 'Serviços',
        requiredPermission: 'view_services',
      },
      {
        id: 'customers',
        icon: Users,
        label: 'Clientes',
        requiredPermission: 'view_customers',
      },
      {
        id: 'products',
        icon: Tags,
        label: 'Produtos',
        requiredPermission: 'view_products',
      },
      {
        id: 'catalog',
        icon: BookOpen,
        label: 'Catálogo',
        requiredPermission: 'view_catalog',
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
        requiredPermission: 'view_enterprise',
      },
      {
        id: 'employees',
        icon: IdCard,
        label: 'Funcionários',
        requiredPermission: 'view_employees',
      },
    ],
  },
] as const;
