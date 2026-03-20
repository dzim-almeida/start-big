export type StatusFilter = 'ativos' | 'inativos';
export type ModalMode = 'create' | 'edit' | 'view';

export interface ServicoFilters {
  buscar?: string;
  status?: StatusFilter | 'todos';
}

export interface ServicosStats {
  total: number;
  ativos: number;
  inativos: number;
  media_valor: number;
}

export interface ServicoFormData {
  descricao: string;
  valor: number;
}

export interface QueryParams {
  page?: number;
  limit?: number;
}

export interface ServicosQuerySearch extends QueryParams {
  search?: string;
  active?: boolean;
}
