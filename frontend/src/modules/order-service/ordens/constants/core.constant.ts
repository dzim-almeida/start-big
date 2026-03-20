export const BASE_ORDER_SERVICE_URL = "/ordens-servico"
export const BASE_EMPLOYEE_OS_URL = "/funcionarios"
export const BASE_CUSTOMER_OS_URL = "/clientes"

export const ORDER_SERVICE_QUERY_KEY = "order-service-query"
export const ORDER_SERVICE_STATS_QUERY_KEY = "order-service-stats-query"
export const ORDER_SERVICE_QUERY_STALE_TIME = 1000 * 60

export const OS_EMPLOYEE_QUERY_KEY = "os-employee-query"
export const OS_EMPLOYEE_QUERY_STALE_TIME = 1000 * 60

export const OS_CUSTOMER_QUERY_KEY = "os-customer-query"
export const OS_CUSTOMER_QUERY_STALE_TIME = 1000 * 60


export const DEFAULT_OS_CREATE_VALUES = {
  prioridade: 'NORMAL' as const,
  defeito_relatado: '',
  diagnostico: undefined,
  solucao: undefined,
  senha_aparelho: undefined,
  acessorios: undefined,
  condicoes_aparelho: undefined,
  observacoes: undefined,
  desconto: undefined,
  garantia: undefined,
  data_previsao: undefined,
  cliente_id: undefined,
  funcionario_id: undefined,
  equipamento: {
    tipo_equipamento: 'OUTROS' as const,
    marca: '',
    modelo: '',
    numero_serie: '',
    imei: '',
    cor: undefined,
  },
  itens: [] as never[],
}

export const DEFAULT_OS_ITEM_VALUES = {
  tipo: 'SERVICO' as const,
  nome: '',
  unidade_medida: 'UN' as const,
  quantidade: 1,
  valor_unitario: 0,
}

export const DEFAULT_OS_PAGAMENTO_VALUES = {
  forma_pagamento_id: 0,
  valor: 0,
  parcelas: 1,
  bandeira_cartao: undefined,
  detalhes: undefined,
}