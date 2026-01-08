import {
  ShoppingCart,
  LayoutDashboard,
  Package,
  Tags,
  Users,
  BookOpen,
  Building,
  IdCard
} from 'lucide-vue-next';

import { sidebarSection } from "../types/mainLayout.types";

export const SIDEBAR_SECTIONS: sidebarSection[] = [
    {
        title: 'MENU PRINCIPAL',
        options: [
            {
                id: 'home',
                icon: LayoutDashboard,
                label: 'Início',
            },
            {
                id: 'sales',
                icon: ShoppingCart,
                label: 'Vendas',
            },
            {
                id: 'storage',
                icon: Package,
                label: 'Estoque',
            },
            {
                id: 'customers',
                icon: Users,
                label: 'Clientes',
            },
            {
                id: 'products',
                icon: Tags,
                label: 'Produtos',
            },
            {
                id: 'catalog',
                icon: BookOpen,
                label: 'Catálogo',
            },
        ]
    },
    {
        title: 'EMPRESA',
        options: [
            {
                id: 'enterprise',
                icon: Building,
                label: 'Dados da Empresa',
            },
            {
                id: 'employees',
                icon: IdCard,
                label: 'Funcionários',
            },
        ]
    }
] as const;