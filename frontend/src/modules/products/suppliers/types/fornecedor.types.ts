// ============================================================================
// MÓDULO: FornecedorTypes (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Centralizar as definições de tipos TypeScript do módulo.
// FUNCIONALIDADES: Tipagem para filtros, modos de modal (CRUD) e estrutura 
//                  de dados do formulário de fornecedores/entregadores.
// ============================================================================
export type StatusFilter = 'ativos' | 'inativos';
export type ModalMode = 'create' | 'edit' | 'view';
/** 'arquiteto' (marcenaria, Spec 09B D2): quem indica clientes e recebe RT. */
export type SupplierTipo = 'produto' | 'transportadora' | 'entregador' | 'arquiteto';

export interface FornecedorFilters {
  buscar?: string;
  status?: StatusFilter | 'todos';
}

export interface EnderecoFormData {
  endereco_id: number | null;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;
  cep: string;
}

export interface FornecedorFormData extends EnderecoFormData {
  tipo: SupplierTipo;
  /** Só do formulário (não vai para a API): o arquiteto é pessoa física (CPF) ou jurídica (CNPJ). */
  pessoa: 'PF' | 'PJ';
  nome: string;
  cnpj: string;
  cpf: string;
  nome_fantasia: string;
  ie: string;
  telefone: string;
  celular: string;
  email: string;
  representante: string;
  veiculo: string;
  placa: string;
  observacao: string;
  banco: string;
  agencia: string;
  conta: string;
  tipo_conta: string;
  pix: string;
}
