export interface OSItemForm {
  tipo?: string;
  nome?: string;
  descricao?: string;
  servico_id?: string | number;
  produto_id?: string | number;
  quantidade: number;
  valor_unitario: number;
  unidade_medida?: string;
}
