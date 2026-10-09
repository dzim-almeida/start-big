/**
 * @fileoverview Permission keys and endpoint mapping
 * @description Centralizes permission references for UI and API resources
 */

export const PERMISSIONS = {
  all: 'all',
  dashboard: 'view_dashboard',
  sales: 'view_sales',
  storage: 'view_storage',
  services: 'servico',
  customers: 'cliente',
  products: 'produto',
  catalog: 'view_catalog',
  enterprise: 'empresa',
  employees: 'funcionario',
  positions: 'cargo',
  suppliers: 'fornecedor',
  reports: 'view_reports',
  /**
   * Consultar o financeiro: ver contas, saldos e o resultado do mês.
   *
   * Separado de `manageFinance` de propósito. Contas a Pagar mostra aluguel e
   * salário; cobrar um cliente que ficou para o fim do mês não. Sem os dois
   * eixos, dar acesso à cobrança abriria a folha de pagamento junto.
   */
  finance: 'view_financeiro',
  /** Lançar, dar baixa e estornar. Inclui o que `finance` já permite ver. */
  manageFinance: 'manage_financeiro',
  /** Etiquetas: ver a aba e imprimir (qualquer caixa da linha Etiquetas). */
  labels: 'etiqueta',
  /** Criar e editar modelos de etiqueta. */
  manageLabels: 'manage_labels',
  /** Apagar modelos — some de todos os terminais da loja. */
  deleteLabels: 'delete_labels',
  /**
   * Compras: ver fornecedores do produto (e, nas próximas fases, pedidos).
   * Qualquer caixa da linha "Compras" da tela de Cargos.
   */
  purchases: 'compra',
  /** Cadastrar fornecedores do produto e fazer pedidos de compra. */
  managePurchases: 'manage_purchases',
  /**
   * Ver PREÇO de compra. Não é o `purchases`: este aceita a chave genérica
   * `compra`, que na fase 3 vai estar ligada também para quem só recebe
   * mercadoria — e o almoxarife confere sem ver preço (plano de compras, D14).
   */
  viewPurchaseCosts: 'view_purchases',
  /** Cancelar pedido de compra: desfaz um compromisso já mandado ao fornecedor. */
  cancelPurchases: 'delete_purchases',
  /**
   * Linha "Recebimento" de Cargos (o almoxarife): ver os pedidos a receber,
   * SEM preço. Chave própria, separada de `compra`, porque quem só recebe não
   * pode herdar o que a linha Compras libera.
   */
  receiving: 'recebimento_compra',
  /** Dar entrada no que chegou. Quem gerencia compras também pode. */
  receivePurchases: 'receive_purchases',
  /** Qualquer uma das duas linhas: decide se o grupo "Compras" do menu aparece. */
  purchasesAny: 'compras_ou_recebimento',
  /**
   * Linha "Fábrica" de Cargos (só marcenaria). Visualizar = ver custo e margem
   * do orçamento; Gerenciar = orçar, enviar, registrar a resposta do cliente e
   * liberar compra antes do sinal.
   */
  viewFabricaCustos: 'view_fabrica',
  manageFabrica: 'manage_fabrica',
  /**
   * Linha "Custos da Marcenaria" de Cargos (Spec 04A/04B). Ver custo, margem,
   * markup, perda e RT do orçamento. A MESMA chave que o backend confere.
   */
  viewCustosMarcenaria: 'view_custos_marcenaria',
  /** Alterar os parâmetros de preço da marcenaria. Inclui o que `view` permite. */
  manageCustosMarcenaria: 'manage_custos_marcenaria',
} as const;

export type PermissionKey = typeof PERMISSIONS[keyof typeof PERMISSIONS];

export const ENDPOINT_PERMISSION_MAP = {
  cargos: PERMISSIONS.positions,
  funcionarios: PERMISSIONS.employees,
  produtos: PERMISSIONS.products,
  fornecedores: PERMISSIONS.suppliers,
  servicos: PERMISSIONS.services,
  clientes: PERMISSIONS.customers,
  empresas: PERMISSIONS.enterprise,
} as const;

export const PERMISSION_ALIASES: Partial<Record<PermissionKey, string[]>> = {
  [PERMISSIONS.dashboard]: ['view_dashboard', 'manage_dashboard', 'delete_dashboard'],
  [PERMISSIONS.sales]: ['view_sales', 'manage_sales', 'delete_sales'],
  [PERMISSIONS.storage]: ['view_storage', 'manage_storage', 'delete_storage'],
  [PERMISSIONS.services]: ['view_services', 'manage_services', 'delete_services'],
  [PERMISSIONS.customers]: ['view_customers', 'manage_customers', 'delete_customers'],
  [PERMISSIONS.products]: ['view_products', 'manage_products', 'delete_products'],
  [PERMISSIONS.catalog]: ['view_catalog', 'manage_catalog', 'delete_catalog'],
  [PERMISSIONS.enterprise]: ['view_enterprise', 'manage_enterprise', 'delete_enterprise'],
  [PERMISSIONS.employees]: ['view_employees', 'manage_employees', 'delete_employees'],
  [PERMISSIONS.positions]: ['view_positions', 'manage_positions', 'delete_positions'],
  [PERMISSIONS.reports]: ['view_reports', 'manage_reports'],
  // Quem pode lançar também pode ver: sem este alias, um cargo marcado só com
  // `manage_financeiro` conseguiria dar baixa numa conta e mesmo assim não
  // enxergaria a tela que a lista.
  [PERMISSIONS.finance]: ['view_financeiro', 'manage_financeiro'],
  [PERMISSIONS.manageFinance]: ['manage_financeiro'],
  [PERMISSIONS.labels]: ['view_labels', 'manage_labels', 'delete_labels'],
  [PERMISSIONS.manageLabels]: ['manage_labels'],
  [PERMISSIONS.deleteLabels]: ['delete_labels'],
  [PERMISSIONS.purchases]: ['view_purchases', 'manage_purchases', 'delete_purchases'],
  [PERMISSIONS.managePurchases]: ['manage_purchases'],
  [PERMISSIONS.viewPurchaseCosts]: ['view_purchases', 'manage_purchases', 'delete_purchases'],
  [PERMISSIONS.cancelPurchases]: ['delete_purchases'],
  [PERMISSIONS.receiving]: ['view_receiving', 'receive_purchases'],
  [PERMISSIONS.receivePurchases]: ['receive_purchases', 'manage_purchases'],
  [PERMISSIONS.viewFabricaCustos]: ['view_fabrica', 'manage_fabrica'],
  [PERMISSIONS.manageFabrica]: ['manage_fabrica'],
  // Quem gere os parâmetros da marcenaria também vê os custos (Spec 04A, D8).
  [PERMISSIONS.viewCustosMarcenaria]: ['manage_custos_marcenaria'],
  [PERMISSIONS.purchasesAny]: [
    'compra', 'view_purchases', 'manage_purchases', 'delete_purchases',
    'recebimento_compra', 'view_receiving', 'receive_purchases',
  ],
};
