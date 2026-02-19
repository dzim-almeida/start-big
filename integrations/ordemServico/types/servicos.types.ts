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
