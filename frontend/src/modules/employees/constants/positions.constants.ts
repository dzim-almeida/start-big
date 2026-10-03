/**
 * @fileoverview Constants for cargo (position) UI
 * @description Permission matrix configuration and card themes
 */

import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Wrench,
  Users,
  Tags,
  BarChart3,
  Building,
  IdCard,
  ShieldCheck,
  Wallet,
  Printer,
  ClipboardList,
  PackageCheck,
} from 'lucide-vue-next';

import { MODULOS } from '@/shared/constants/modulos.constants';
import { PERMISSIONS } from '@/shared/constants/permissions.constants';
import type { FilterOption } from '@/shared/types/filter.types';
import type {
  AccessLevelDefinition,
  AccessLevelId,
  PermissionMatrixItem,
  PositionCardTheme,
} from '../types/positions.types';

export const POSITION_CARD_THEMES: PositionCardTheme[] = [
  {
    accent: 'bg-blue-500',
    iconBg: 'bg-blue-50 text-blue-600',
    ring: 'ring-blue-200/60',
    glow: 'shadow-blue-100',
  },
];

export const ACCESS_LEVELS: AccessLevelDefinition[] = [
  {
    id: 'administrator',
    label: 'Administrador',
    description: 'Acesso total aos modulos e configuracoes sensiveis.',
    badge: 'Nivel maximo',
    gradient: 'from-indigo-600 to-blue-600',
    minRatio: 0.85,
    filterColor: 'bg-indigo-500',
  },
  {
    id: 'manager',
    label: 'Gestor',
    description: 'Controle amplo com foco em performance e time.',
    badge: 'Nivel avancado',
    gradient: 'from-emerald-500 to-teal-500',
    minRatio: 0.55,
    filterColor: 'bg-emerald-500',
  },
  {
    id: 'operational',
    label: 'Operacional',
    description: 'Permissoes essenciais para rotina e processos.',
    badge: 'Nivel operacional',
    gradient: 'from-amber-500 to-orange-500',
    minRatio: 0.25,
    filterColor: 'bg-amber-500',
  },
  {
    id: 'restricted',
    label: 'Restrito',
    description: 'Acesso limitado para funcoes especificas.',
    badge: 'Nivel inicial',
    gradient: 'from-zinc-500 to-zinc-700',
    minRatio: 0,
    filterColor: 'bg-zinc-500',
  },
];

export const PERMISSION_MATRIX: PermissionMatrixItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    description: 'Indicadores e visao geral',
    icon: LayoutDashboard,
    viewKey: 'view_dashboard',
    manageKey: 'manage_dashboard',
    deleteKey: 'delete_dashboard',
  },
  {
    id: 'sales',
    label: 'Vendas',
    description: 'Operacoes comerciais e PDV',
    icon: ShoppingCart,
    viewKey: 'view_sales',
    manageKey: 'manage_sales',
    deleteKey: 'delete_sales',
  },
  {
    id: 'storage',
    label: 'Estoque',
    description: 'Controle de inventario e entradas',
    icon: Package,
    viewKey: 'view_storage',
    manageKey: 'manage_storage',
    deleteKey: 'delete_storage',
  },
  {
    id: 'services',
    label: 'Servicos',
    description: 'Gestao de atendimentos e OS',
    icon: Wrench,
    viewKey: 'view_services',
    manageKey: 'manage_services',
    deleteKey: 'delete_services',
  },
  {
    id: 'customers',
    label: 'Clientes',
    description: 'Carteira de clientes e historico',
    icon: Users,
    viewKey: 'view_customers',
    manageKey: 'manage_customers',
    deleteKey: 'delete_customers',
  },
  {
    id: 'products',
    label: 'Produtos',
    description: 'Cadastro e catalogo interno',
    icon: Tags,
    viewKey: 'view_products',
    manageKey: 'manage_products',
    deleteKey: 'delete_products',
  },
  {
    id: 'labels',
    label: 'Etiquetas',
    description: 'Imprimir etiquetas e editar modelos',
    icon: Printer,
    // Visualizar = ver a aba e imprimir; Gerenciar = criar e editar modelos;
    // Excluir = apagar modelos (some de todos os terminais da loja).
    viewKey: 'view_labels',
    manageKey: 'manage_labels',
    deleteKey: 'delete_labels',
  },
  {
    id: 'purchases',
    label: 'Compras',
    description: 'Fornecedores do produto e pedidos de compra',
    icon: ClipboardList,
    // Visualizar = ver necessidades, pedidos e precos de compra;
    // Gerenciar = fornecedores do produto, criar/editar/enviar pedidos;
    // Excluir = CANCELAR pedido (desfaz o que ja foi mandado ao fornecedor).
    viewKey: 'view_purchases',
    manageKey: 'manage_purchases',
    deleteKey: 'delete_purchases',
    modulo: MODULOS.COMPRAS,
  },
  {
    id: 'purchase_receiving',
    label: 'Recebimento',
    description: 'Conferir e dar entrada na mercadoria comprada',
    icon: PackageCheck,
    // Para o almoxarife: confere QUANTIDADE, nunca ve preco (plano de compras,
    // D14). Visualizar = ver os pedidos a receber; Gerenciar = dar entrada.
    viewKey: 'view_receiving',
    manageKey: 'receive_purchases',
    modulo: MODULOS.COMPRAS,
  },
  {
    id: 'reports',
    label: 'Relatorios',
    description: 'Faturamento, ranking e comissoes',
    icon: BarChart3,
    viewKey: 'view_reports',
    manageKey: 'manage_reports',
    // Read-only: sem acao de excluir.
  },
  {
    id: 'finance',
    label: 'Financeiro',
    description: 'Contas a pagar, a receber e resultado',
    icon: Wallet,
    viewKey: 'view_financeiro',
    manageKey: 'manage_financeiro',
    // Sem acao de excluir, e nao por esquecimento: lancamento financeiro nao se
    // apaga, se estorna. Oferecer o botao aqui prometeria uma operacao que o
    // modulo nao vai ter.
  },
  {
    id: 'enterprise',
    label: 'Empresa',
    description: 'Dados e configuracoes gerais',
    icon: Building,
    viewKey: 'view_enterprise',
    manageKey: 'manage_enterprise',
    deleteKey: 'delete_enterprise',
  },
  {
    id: 'employees',
    label: 'Equipe',
    description: 'Funcionarios, jornadas e acessos',
    icon: IdCard,
    viewKey: 'view_employees',
    manageKey: 'manage_employees',
    deleteKey: 'delete_employees',
  },
  {
    id: 'roles',
    label: 'Cargos',
    description: 'Permissoes e perfis internos',
    icon: ShieldCheck,
    viewKey: 'view_positions',
    manageKey: 'manage_positions',
    deleteKey: 'delete_positions',
  },
];

function chavesDe(itens: PermissionMatrixItem[]): string[] {
  return Array.from(
    new Set(
      itens.flatMap((item) =>
        [item.viewKey, item.manageKey, item.deleteKey].filter(
          (key): key is string => Boolean(key),
        ),
      ),
    ),
  );
}

/**
 * As caixas que contam no nivel do cargo (Administrador, Gestor...): so as dos
 * modulos que toda loja tem. As dos modulos contrataveis (`modulo`) ficam de
 * fora de proposito -- contar Compras rebaixaria o nivel de todo cargo ja
 * cadastrado no dia da atualizacao, numa loja que nem contratou o modulo.
 */
export const PERMISSION_KEYS = chavesDe(PERMISSION_MATRIX.filter((item) => !item.modulo));

/** Todas as caixas, inclusive as dos modulos contrataveis. */
export const ALL_PERMISSION_KEYS = chavesDe(PERMISSION_MATRIX);

export const MODULE_PERMISSION_MAP: Partial<Record<PermissionMatrixItem['id'], string>> = {
  sales: 'venda',
  services: PERMISSIONS.services,
  customers: PERMISSIONS.customers,
  products: PERMISSIONS.products,
  labels: PERMISSIONS.labels,
  purchases: PERMISSIONS.purchases,
  // Chave PROPRIA, nao `compra`: duas linhas gravando a mesma chave fariam a
  // segunda sobrescrever a primeira em `applyEndpointPermissions`.
  purchase_receiving: PERMISSIONS.receiving,
  enterprise: PERMISSIONS.enterprise,
  employees: PERMISSIONS.employees,
  roles: PERMISSIONS.positions,
};

export function buildPermissionDefaults(): Record<string, boolean> {
  return ALL_PERMISSION_KEYS.reduce(
    (acc, key) => {
      acc[key] = false;
      return acc;
    },
    {} as Record<string, boolean>,
  );
}

export function applyEndpointPermissions(permissoes: Record<string, boolean>) {
  const updated = { ...permissoes };

  PERMISSION_MATRIX.forEach((module) => {
    const permissionKey = MODULE_PERMISSION_MAP[module.id];
    if (!permissionKey) return;

    const hasAny = [module.viewKey, module.manageKey, module.deleteKey].some(
      (key) => key && updated[key],
    );

    updated[permissionKey] = hasAny;
  });

  return updated;
}

export function getPermissionStats(
  permissoes: Record<string, boolean> | undefined,
) {
  if (permissoes?.all === true) {
    const total = PERMISSION_KEYS.length;
    return { enabled: total, total, ratio: 1 };
  }
  const enabled = PERMISSION_KEYS.reduce(
    (count, key) => count + (permissoes?.[key] ? 1 : 0),
    0,
  );
  const total = PERMISSION_KEYS.length;
  const ratio = total ? enabled / total : 0;
  return { enabled, total, ratio };
}

export function getAccessLevel(
  permissoes: Record<string, boolean> | undefined,
): AccessLevelDefinition {
  const { ratio } = getPermissionStats(permissoes);
  return (
    ACCESS_LEVELS.find((level) => ratio >= level.minRatio) ||
    ACCESS_LEVELS[ACCESS_LEVELS.length - 1]
  );
}

export const POSITION_LEVEL_FILTERS: Record<AccessLevelId, FilterOption> =
  ACCESS_LEVELS.reduce(
    (acc, level) => {
      acc[level.id] = {
        label: level.label,
        class: '',
        color: level.filterColor,
      };
      return acc;
    },
    {} as Record<AccessLevelId, FilterOption>,
  );
