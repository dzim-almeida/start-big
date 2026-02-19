// ===========================================================================
// IMPORTS DE TIPOS COMPARTILHADOS
// ===========================================================================

// Tipos comuns (compartilhados entre módulos)
export type { ClienteResumo, FuncionarioResumo } from '@/shared/types/common.types';
import type { ClienteResumo, FuncionarioResumo } from '@/shared/types/common.types';

// Tipos do módulo financeiro
export type { FormaPagamentoRead } from '@/modules/financeiro/types/financeiro.types';
import type { FormaPagamentoRead } from '@/modules/financeiro/types/financeiro.types';

// ===========================================================================
// ENUMS E TIPOS BASE
// ===========================================================================

export type OrdemServicoStatus =
  | 'ABERTA'
  | 'EM_ANDAMENTO'
  | 'AGUARDANDO_PECAS'
  | 'AGUARDANDO_APROVACAO'
  | 'AGUARDANDO_RETIRADA'
  | 'FINALIZADA'
  | 'CANCELADA';

export type OrdemServicoPrioridade = 'BAIXA' | 'NORMAL' | 'ALTA' | 'URGENTE';

// ===========================================================================
// FILTROS
// ===========================================================================

export interface OSFilters {
  buscar?: string;
  status?: OrdemServicoStatus | 'todos';
  cliente_id?: number;
  funcionario_id?: number;
  page?: number;
  limit?: number;
}

// ===========================================================================
// ITEM DE OS
// ===========================================================================

export interface OrdemServicoItemCreate {
  servico_id?: number;
  descricao: string;
  quantidade: number;
  valor_unitario: number;
}

export interface OrdemServicoItemRead extends OrdemServicoItemCreate {
  id: number;
  ordem_servico_id: number;
  valor_total: number;
}

export interface OrdemServicoItemUpdate {
  id?: number;
  servico_id?: number;
  descricao?: string;
  quantidade?: number;
  valor_unitario?: number;
}

export interface OrdemServicoFotoRead {
  id: number;
  ordem_servico_id: number;
  nome_arquivo: string;
  url: string;
  data_criacao: string;
}

export interface OrdemServicoCreate {
  cliente_id: number;
  funcionario_id?: number;
  prioridade?: OrdemServicoPrioridade;
  equipamento: string;
  marca?: string;
  modelo?: string;
  numero_serie?: string;
  imei?: string;
  cor?: string;
  senha_aparelho?: string;
  acessorios?: string;
  condicoes_aparelho?: string;
  defeito_relatado: string;
  diagnostico?: string;
  observacoes?: string;
  data_previsao?: string;
  desconto?: number;
  valor_entrada?: number;
  forma_pagamento?: string;
  garantia?: string;
  itens?: OrdemServicoItemCreate[];
}

export interface OrdemServicoRead {
  id: number;
  numero: string;
  cliente_id: number;
  funcionario_id?: number;
  status: OrdemServicoStatus;
  prioridade: OrdemServicoPrioridade;
  equipamento: string;
  marca?: string;
  modelo?: string;
  numero_serie?: string;
  imei?: string;
  cor?: string;
  senha_aparelho?: string;
  acessorios?: string;
  condicoes_aparelho?: string;
  defeito_relatado: string;
  diagnostico?: string;
  solucao?: string;
  observacoes?: string;
  valor_total: number;
  desconto: number;
  valor_entrada: number;
  forma_pagamento?: string;
  garantia?: string;
  data_previsao?: string | Date;
  data_finalizacao?: string | Date;
  data_criacao: string | Date;
  data_atualizacao: string | Date;
  ativo: boolean;
  cliente?: ClienteResumo;
  funcionario?: FuncionarioResumo;
  itens: OrdemServicoItemRead[];
  pagamentos: OSPagamentoRead[];
  fotos: OrdemServicoFotoRead[];
}

export interface OSPagamentoRead {
  id: number;
  forma_pagamento_id: number;
  valor: number;
  parcelas: number;
  bandeira_cartao?: string;
  detalhes?: Record<string, any>;
  forma_pagamento?: FormaPagamentoRead;
}

export interface OrdemServicoListRead {
  id: number;
  numero: string;
  cliente_id: number;
  funcionario_id?: number;
  status: OrdemServicoStatus;
  prioridade: OrdemServicoPrioridade;
  equipamento: string;
  defeito_relatado: string;
  valor_total: number;
  data_previsao?: string | Date;
  data_criacao: string | Date;
  ativo: boolean;
  cliente?: ClienteResumo;
  funcionario?: FuncionarioResumo;
}

export interface OrdemServicoUpdate {
  funcionario_id?: number;
  status?: OrdemServicoStatus;
  prioridade?: OrdemServicoPrioridade;
  equipamento?: string;
  marca?: string;
  modelo?: string;
  numero_serie?: string;
  imei?: string;
  cor?: string;
  senha_aparelho?: string;
  acessorios?: string;
  condicoes_aparelho?: string;
  defeito_relatado?: string;
  diagnostico?: string;
  solucao?: string;
  observacoes?: string;
  data_previsao?: string;
  data_finalizacao?: string;
  desconto?: number;
  valor_entrada?: number;
  forma_pagamento?: string;
  garantia?: string;
  itens?: OrdemServicoItemUpdate[];
}

export interface OSPagamentoCreate {
  forma_pagamento_id: number;
  valor: number;
  parcelas: number;
  bandeira_cartao?: string;
  detalhes?: Record<string, any>;
}

export interface OrdemServicoFinalizar {
  solucao: string;
  observacoes?: string;
  pagamentos: OSPagamentoCreate[];
  desconto?: number;
}

export interface PaginatedOrdensServico {
  items: OrdemServicoListRead[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface OSEstatisticas {
  total: number;
  abertas: number;
  em_andamento: number;
  finalizadas: number;
  canceladas: number;
}

