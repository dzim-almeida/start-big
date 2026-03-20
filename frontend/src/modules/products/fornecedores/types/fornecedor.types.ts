export type StatusFilter = 'ativos' | 'inativos';
export type ModalMode = 'create' | 'edit' | 'view';

export interface FornecedorFilters {
  buscar?: string;
  status?: StatusFilter | 'todos';
}

export interface FornecedorFormData {
  nome: string;
  cnpj: string;
  nome_fantasia: string;
  ie: string;
  telefone: string;
  celular: string;
  email: string;
  representante: string;
}
