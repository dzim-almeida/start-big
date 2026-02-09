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

export interface ServicoCreate {
  descricao: string;
  valor: number;
}

export interface ServicoRead {
  id: number;
  descricao: string;
  valor: number;
  ativo: boolean;
}

export interface ServicoUpdate {
  descricao?: string;
  valor?: number;
}

export interface ServicoFormData {
  descricao: string;
  valor: number;
}
